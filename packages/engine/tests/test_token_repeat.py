"""Tests for the token repetition detector."""

from inferencebrake.detectors.token_repeat import TokenRepeatDetector, _tokenize
from inferencebrake.types import (
    DetectorVerdict,
    SessionState,
    StepRecord,
    ThresholdConfig,
)


def make_session(texts):
    session = SessionState(session_id="test")
    for i, text in enumerate(texts):
        session.add_step(StepRecord(step_number=i + 1, reasoning=text))
    return session


def test_tokenize_lowercases_and_strips_punctuation():
    assert _tokenize("Hello, World! It's fine.") == ["hello", "world", "it's", "fine"]


def test_intra_text_repetition_detected():
    reasoning = (
        "I need to check the weather in New York City. "
        "Let me call the weather API. "
        "I need to check the weather in New York City. "
        "Let me call the weather API."
    )
    signal = TokenRepeatDetector().detect(reasoning, make_session([]), ThresholdConfig())

    assert signal.verdict == DetectorVerdict.LOOP_DETECTED
    assert signal.metadata["intra_span"] >= 6
    assert signal.metadata["source"] == "intra"


def test_clean_reasoning_is_safe():
    reasoning = (
        "First I parse the request, then I validate the inputs, "
        "and finally I write the result to disk."
    )
    signal = TokenRepeatDetector().detect(reasoning, make_session([]), ThresholdConfig())

    assert signal.verdict == DetectorVerdict.SAFE
    assert "No significant repetition" in signal.detail


def test_cross_step_repetition_detected():
    text = "The upstream service returned a transient error so I will retry the same call"
    session = make_session([text])
    signal = TokenRepeatDetector().detect(text, session, ThresholdConfig())

    assert signal.verdict == DetectorVerdict.LOOP_DETECTED
    assert signal.metadata["source"] == "cross"


def test_short_repeated_span_warns():
    reasoning = (
        "alpha beta gamma delta epsilon then something else "
        "alpha beta gamma delta epsilon"
    )
    signal = TokenRepeatDetector().detect(reasoning, make_session([]), ThresholdConfig())

    assert signal.verdict == DetectorVerdict.WARNING
    assert signal.metadata["span_len"] == 5


def test_too_few_tokens_is_safe():
    signal = TokenRepeatDetector().detect("hi there", make_session([]), ThresholdConfig())
    assert signal.verdict == DetectorVerdict.SAFE


def test_pipeline_registers_token_repeat():
    from inferencebrake.pipeline import DetectionPipeline
    from inferencebrake.types import PipelineConfig

    pipeline = DetectionPipeline(PipelineConfig())
    assert "token_repeat" in pipeline._detectors
