"""Unit tests for the detectors that previously had no dedicated coverage.

Covers: ngram, editdist, compression, entropy, cusum, action, semantic.
token_repeat has its own suite in test_token_repeat.py.
"""

import pytest

from inferencebrake.detectors.action import (
    ActionDetector,
    _find_cycle,
    _find_direct_repeat,
    _find_stutter_cycle,
)
from inferencebrake.detectors.compression import (
    CompressionDetector,
    _ncd_similarity,
)
from inferencebrake.detectors.cusum import CUSUMDetector
from inferencebrake.detectors.editdist import (
    EditDistanceDecayDetector,
    _compute_trend,
    _levenshtein_distance,
    _normalized_edit_distance,
)
from inferencebrake.detectors.entropy import (
    EntropyDetector,
    _information_density,
    _vocabulary_diversity,
    _word_entropy,
)
from inferencebrake.detectors.ngram import NgramDetector, _extract_ngrams, _normalize
from inferencebrake.detectors.semantic import (
    SemanticDetector,
    cosine_similarity,
    pairwise_similarities,
)
from inferencebrake.types import (
    DetectorVerdict,
    LoopType,
    SessionState,
    StepRecord,
    ThresholdConfig,
)


def make_session(texts, embeddings=None):
    session = SessionState(session_id="test")
    for i, text in enumerate(texts):
        embedding = embeddings[i] if embeddings else None
        session.add_step(StepRecord(step_number=i + 1, reasoning=text, embedding=embedding))
    return session


# --------------------------------------------------------------------------
# ngram
# --------------------------------------------------------------------------


def test_ngram_normalize_strips_punctuation_and_case():
    assert _normalize("Hello, World!") == "hello world"


def test_ngram_extract_ngrams_word_level():
    grams = _extract_ngrams("the quick brown fox", 2)
    assert ("the", "quick") in grams
    assert len(grams) == 3


def test_ngram_detects_repeated_sentences_across_steps():
    text = "I should check the weather in New York City. Let me call the weather API."
    session = make_session([text, text])
    signal = NgramDetector().detect(text, session, ThresholdConfig())

    assert signal.verdict == DetectorVerdict.LOOP_DETECTED
    assert signal.loop_type == LoopType.EXACT_REPETITION


def test_ngram_clean_reasoning_is_safe():
    session = make_session([
        "First I parse the incoming request and validate every field.",
        "Then I persist the record and return the new identifier.",
    ])
    signal = NgramDetector().detect(
        "Finally I emit a structured log line for the audit trail.",
        session,
        ThresholdConfig(),
    )

    assert signal.verdict == DetectorVerdict.SAFE


def test_ngram_not_enough_history_is_safe():
    signal = NgramDetector().detect("anything", make_session([]), ThresholdConfig())
    assert signal.verdict == DetectorVerdict.SAFE


# --------------------------------------------------------------------------
# editdist
# --------------------------------------------------------------------------


def test_levenshtein_distance_known_values():
    assert _levenshtein_distance("kitten", "sitting") == 3
    assert _levenshtein_distance("", "abc") == 3
    assert _levenshtein_distance("same", "same") == 0


def test_normalized_edit_distance_bounds():
    assert _normalized_edit_distance("abc", "abc") == 0.0
    assert _normalized_edit_distance("abc", "xyz") == 1.0


def test_compute_trend_direction():
    assert _compute_trend([1.0, 0.5, 0.0]) < 0
    assert _compute_trend([0.0, 0.5, 1.0]) > 0
    assert _compute_trend([0.5]) == 0.0


def test_editdist_detects_decay_toward_fixed_point():
    base = "the agent retries the upstream call and receives the same transient error"
    varied = "unrelated opening step about parsing configuration files and schemas"
    session = make_session([varied, base, base])

    signal = EditDistanceDecayDetector().detect(base, session, ThresholdConfig())

    assert signal.verdict == DetectorVerdict.LOOP_DETECTED
    assert signal.loop_type == LoopType.PARAPHRASE_LOOP
    assert signal.metadata["current_delta_i"] < 0.08


def test_editdist_healthy_reasoning_is_safe():
    texts = [
        "first I read the configuration file and parse every declared field",
        "next I open a connection to the upstream service and verify the handshake",
        "then I stream the payload and write each chunk to the destination buffer",
        "finally I close the handles and emit a summary of the processed records",
    ]
    session = make_session(texts)
    signal = EditDistanceDecayDetector().detect(
        "afterwards I schedule the retry with an exponential backoff and jitter",
        session,
        ThresholdConfig(),
    )

    assert signal.verdict != DetectorVerdict.LOOP_DETECTED


# --------------------------------------------------------------------------
# compression
# --------------------------------------------------------------------------


def test_ncd_identical_texts_is_high_similarity():
    text = "the agent keeps retrying the same upstream call and gets the same error"
    # Not exactly 1.0: compression framing overhead keeps identical-text NCD high but sub-1.
    assert _ncd_similarity(text, text) > 0.8


def test_ncd_unrelated_texts_is_lower_than_identical():
    a = "the agent keeps retrying the same upstream call and gets the same error"
    b = "a completely different sentence about parsing configuration files safely"
    assert _ncd_similarity(a, b) < _ncd_similarity(a, a)


def test_compression_detects_redundant_step():
    text = (
        "the agent keeps retrying the same upstream call and receives the "
        "same transient error each time"
    )
    session = make_session([text, text, text])
    signal = CompressionDetector().detect(text, session, ThresholdConfig())

    assert signal.verdict == DetectorVerdict.LOOP_DETECTED
    assert signal.loop_type == LoopType.PARAPHRASE_LOOP


def test_compression_clean_reasoning_is_safe():
    session = make_session([
        "parse the inbound request payload and validate the schema version",
        "resolve the tenant configuration from the cache or the primary store",
    ])
    signal = CompressionDetector().detect(
        "write the normalized record to the warehouse and publish an event",
        session,
        ThresholdConfig(),
    )

    assert signal.verdict != DetectorVerdict.LOOP_DETECTED


# --------------------------------------------------------------------------
# entropy
# --------------------------------------------------------------------------


def test_word_entropy_repetitive_is_lower_than_diverse():
    repetitive = "the the the the the the the the"
    diverse = "alpha beta gamma delta epsilon zeta eta theta"
    assert _word_entropy(repetitive) < _word_entropy(diverse)


def test_vocabulary_diversity_type_token_ratio():
    assert _vocabulary_diversity("a a a a") == pytest.approx(0.25)
    assert _vocabulary_diversity("a b c d") == pytest.approx(1.0)


def test_information_density_counts_content_words():
    assert _information_density("the a of and") == pytest.approx(0.0)
    assert _information_density("widget parser serializer") == pytest.approx(1.0)


def test_entropy_detects_collapse():
    low = "the the the the the the the the"
    session = make_session([low, low])
    detector = EntropyDetector()
    config = ThresholdConfig()

    detector.detect(low, session, config)
    detector.detect(low, session, config)
    signal = detector.detect(low, session, config)

    assert signal.verdict == DetectorVerdict.LOOP_DETECTED
    assert signal.loop_type == LoopType.ENTROPY_COLLAPSE


def test_entropy_diverse_reasoning_is_safe():
    session = make_session([
        "parse the payload and validate every declared field before use",
        "resolve the tenant configuration from the distributed cache layer",
    ])
    detector = EntropyDetector()
    config = ThresholdConfig()
    diverse = "serialize the normalized record and publish a domain event downstream"

    signal = None
    for _ in range(3):
        signal = detector.detect(diverse, session, config)

    assert signal is not None
    assert signal.verdict != DetectorVerdict.LOOP_DETECTED


# --------------------------------------------------------------------------
# cusum
# --------------------------------------------------------------------------


def test_cusum_requires_embedding():
    session = make_session(["a", "b", "c"])
    signal = CUSUMDetector().detect("d", session, ThresholdConfig())
    assert signal.verdict == DetectorVerdict.SAFE


def test_cusum_detects_stagnant_embeddings():
    embedding = [1.0, 0.0, 0.0]
    session = make_session(["a", "b", "c"], embeddings=[embedding, embedding, embedding])

    signal = CUSUMDetector().detect("d", session, ThresholdConfig(), embedding=embedding)

    assert signal.verdict == DetectorVerdict.LOOP_DETECTED
    assert signal.loop_type == LoopType.CUSUM_STAGNATION


def test_cusum_healthy_drift_is_safe():
    session = make_session(
        ["a", "b", "c"],
        embeddings=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
    )
    signal = CUSUMDetector().detect(
        "d", session, ThresholdConfig(), embedding=[-1.0, 0.0, 0.0]
    )

    assert signal.verdict != DetectorVerdict.LOOP_DETECTED


# --------------------------------------------------------------------------
# action
# --------------------------------------------------------------------------


def test_find_direct_repeat_helper():
    assert _find_direct_repeat(["a", "a", "a"], 3) == ("a", 3)
    assert _find_direct_repeat(["a", "b", "a"], 3) is None


def test_find_cycle_helper():
    assert _find_cycle(["a", "b", "a", "b"], 2, 5) == (["a", "b"], 2)


def test_find_stutter_cycle_helper():
    result = _find_stutter_cycle(["a", "a", "b", "a", "a", "b"], 5)
    assert result is not None
    assert result[1] >= 2


def test_action_direct_repeat_detected():
    session = SessionState(session_id="test")
    session.action_sequence = ["search", "search", "search"]
    signal = ActionDetector().detect("...", session, ThresholdConfig())

    assert signal.verdict == DetectorVerdict.LOOP_DETECTED
    assert signal.loop_type == LoopType.ACTION_REPETITION


def test_action_cycle_detected():
    session = SessionState(session_id="test")
    session.action_sequence = ["read", "write", "read", "write"]
    signal = ActionDetector().detect("...", session, ThresholdConfig())

    assert signal.verdict == DetectorVerdict.LOOP_DETECTED
    assert signal.loop_type == LoopType.STRUCTURAL_LOOP


def test_action_clean_sequence_is_safe():
    session = SessionState(session_id="test")
    session.action_sequence = ["search", "read", "write", "deploy"]
    signal = ActionDetector().detect("...", session, ThresholdConfig())

    assert signal.verdict == DetectorVerdict.SAFE


# --------------------------------------------------------------------------
# semantic
# --------------------------------------------------------------------------


def test_cosine_similarity_bounds():
    assert cosine_similarity([1, 0, 0], [1, 0, 0]) == pytest.approx(1.0)
    assert cosine_similarity([1, 0, 0], [0, 1, 0]) == pytest.approx(0.0)


def test_pairwise_similarities_length_and_values():
    sims = pairwise_similarities([1, 0, 0], [[1, 0, 0], [0, 1, 0]])
    assert len(sims) == 2
    assert sims[0] == pytest.approx(1.0)
    assert sims[1] == pytest.approx(0.0)


def test_semantic_detects_repeat_embedding():
    embedding = [1.0, 0.0, 0.0]
    session = make_session(["a", "b"], embeddings=[embedding, embedding])

    signal = SemanticDetector().detect(
        "c", session, ThresholdConfig(), embedding=embedding
    )

    assert signal.verdict == DetectorVerdict.LOOP_DETECTED
    assert signal.loop_type == LoopType.SEMANTIC_SIMILARITY


def test_semantic_no_embedding_is_safe():
    session = make_session(["a", "b"])
    signal = SemanticDetector().detect("c", session, ThresholdConfig())
    assert signal.verdict == DetectorVerdict.SAFE


def test_semantic_orthogonal_embedding_is_safe():
    session = make_session(["a", "b"], embeddings=[[1, 0, 0], [1, 0, 0]])
    signal = SemanticDetector().detect(
        "c", session, ThresholdConfig(), embedding=[0, 1, 0]
    )

    assert signal.verdict != DetectorVerdict.LOOP_DETECTED


# --------------------------------------------------------------------------
# pipeline registration
# --------------------------------------------------------------------------


def test_pipeline_registers_every_detector():
    from inferencebrake.pipeline import DetectionPipeline
    from inferencebrake.types import PipelineConfig

    pipeline = DetectionPipeline(PipelineConfig())
    for name in (
        "ngram",
        "semantic",
        "cusum",
        "entropy",
        "action",
        "compression",
        "editdist",
        "token_repeat",
    ):
        assert name in pipeline._detectors
