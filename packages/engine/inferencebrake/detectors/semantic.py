"""
Semantic Similarity Detector.

Uses embedding cosine similarity to detect when an agent's reasoning
is semantically revisiting the same ideas even with different wording.

This is the core detection method - the backbone of InferenceBrake.
Works with any embedding model (gte-small via Supabase, or local
sentence-transformers).

The detector compares the current step's embedding against all
embeddings in the session window using cosine similarity.
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np

from inferencebrake.detectors import BaseDetector
from inferencebrake.types import (
    DetectionSignal,
    DetectorVerdict,
    LoopType,
    SessionState,
    ThresholdConfig,
)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a_arr = np.asarray(a, dtype=np.float64)
    b_arr = np.asarray(b, dtype=np.float64)
    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)
    if norm_a < 1e-10 or norm_b < 1e-10:
        return 0.0
    return float(np.dot(a_arr, b_arr) / (norm_a * norm_b))


def pairwise_similarities(
    target: list[float], history: list[list[float]]
) -> list[float]:
    """Compute cosine similarity of target against each vector in history."""
    if not history:
        return []
    target_arr = np.asarray(target, dtype=np.float64)
    history_arr = np.asarray(history, dtype=np.float64)
    # Normalize
    target_norm = target_arr / max(np.linalg.norm(target_arr), 1e-10)
    norms = np.linalg.norm(history_arr, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-10)
    history_norm = history_arr / norms
    # Dot product gives cosine similarity when vectors are normalized
    sims = history_norm @ target_norm
    return sims.tolist()


class SemanticDetector(BaseDetector):
    """
    Embedding-based semantic similarity loop detector.

    Compares the current reasoning step's embedding against
    the N most recent embeddings in the session using cosine similarity.

    When similarity exceeds the threshold, the agent is likely
    revisiting the same reasoning even if the words are different.
    """

    name = "semantic"

    def __init__(self, embedding_fn=None):
        """
        Args:
            embedding_fn: Optional callable(text) -> list[float].
                If provided, will generate embeddings locally.
                If None, expects embeddings to be pre-computed
                and attached to StepRecords.
        """
        self.embedding_fn = embedding_fn

    def detect(
        self,
        reasoning: str,
        session: SessionState,
        config: ThresholdConfig,
        embedding: Optional[list[float]] = None,
        **kwargs,
    ) -> DetectionSignal:
        if session.step_count < config.min_steps_before_detection:
            return self._safe_signal("Not enough history")

        # Get or generate embedding
        if embedding is None and self.embedding_fn is not None:
            embedding = self.embedding_fn(reasoning)
        if embedding is None:
            return self._safe_signal("No embedding available")

        # Get historical embeddings
        history_embeddings = session.get_recent_embeddings(config.similarity_window)
        if not history_embeddings:
            return self._safe_signal("No embeddings in history")

        # Compute similarities
        sims = pairwise_similarities(embedding, history_embeddings)
        if not sims:
            return self._safe_signal("No valid similarities computed")

        max_sim = max(sims)
        max_idx = sims.index(max_sim)
        avg_sim = sum(sims) / len(sims)

        # Semantic Attractor Check
        # Calculate centroid of recent history and distance to it
        # If agent stays close to the centroid for N steps, it's circling an attractor
        if len(history_embeddings) >= 5:
            # Simple centroid of last 5 steps
            recent_group = np.array(history_embeddings[-5:])
            centroid = np.mean(recent_group, axis=0)
            centroid = centroid / np.linalg.norm(centroid) # normalize
            
            # Distance of current embedding to centroid
            dist_to_centroid = 1.0 - cosine_similarity(embedding, centroid.tolist())
            
            # Check if previous steps were also close to their respective centroids
            # (Approximated by checking if they are close to THIS centroid)
            group_dists = [1.0 - cosine_similarity(h, centroid.tolist()) for h in history_embeddings[-5:]]
            avg_dist = sum(group_dists) / len(group_dists)
            
            if dist_to_centroid < 0.1 and avg_dist < 0.15:
                # Tight cluster = semantic attractor
                return DetectionSignal(
                    detector_name=self.name,
                    verdict=DetectorVerdict.LOOP_DETECTED,
                    loop_type=LoopType.SEMANTIC_SIMILARITY,
                    confidence=0.85,
                    score=1.0 - dist_to_centroid,
                    threshold_used=0.1,
                    detail=f"Semantic attractor detected: Agent circling a fixed point (radius {avg_dist:.3f})",
                    metadata={"attractor_radius": avg_dist}
                )

        # Check against threshold
        threshold = config.similarity_threshold
        if max_sim >= threshold:
            # Calculate how many steps back the match is
            steps_back = len(history_embeddings) - max_idx
            return DetectionSignal(
                detector_name=self.name,
                verdict=DetectorVerdict.LOOP_DETECTED,
                loop_type=LoopType.SEMANTIC_SIMILARITY,
                confidence=self._similarity_to_confidence(max_sim, threshold),
                score=max_sim,
                threshold_used=threshold,
                detail=(
                    f"Semantic similarity {max_sim:.3f} >= {threshold:.3f} "
                    f"(matched step {steps_back} steps ago, avg: {avg_sim:.3f})"
                ),
                metadata={
                    "max_similarity": max_sim,
                    "avg_similarity": avg_sim,
                    "all_similarities": sims,
                    "matched_step_offset": steps_back,
                },
            )

        # Warning zone: approaching threshold
        warning_threshold = threshold * 0.85
        if max_sim >= warning_threshold:
            return DetectionSignal(
                detector_name=self.name,
                verdict=DetectorVerdict.WARNING,
                loop_type=LoopType.SEMANTIC_SIMILARITY,
                confidence=self._similarity_to_confidence(max_sim, threshold) * 0.5,
                score=max_sim,
                threshold_used=threshold,
                detail=f"Similarity approaching threshold: {max_sim:.3f} (threshold: {threshold:.3f})",
                metadata={
                    "max_similarity": max_sim,
                    "avg_similarity": avg_sim,
                },
            )

        return self._safe_signal(f"Max similarity: {max_sim:.3f}")

    @staticmethod
    def _similarity_to_confidence(similarity: float, threshold: float) -> float:
        """
        Map similarity above threshold to confidence [0, 1].
        Uses a sigmoid-like curve to amplify differences near threshold.
        """
        if similarity <= threshold:
            return 0.0
        # How far above threshold (0 to ~0.15 range typically)
        excess = similarity - threshold
        max_excess = 1.0 - threshold
        # Sigmoid mapping
        x = excess / max(max_excess, 0.01) * 6 - 3
        return 1.0 / (1.0 + math.exp(-x))
