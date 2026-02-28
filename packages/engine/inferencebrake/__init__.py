"""
InferenceBrake - Multi-layer reasoning loop detection engine.

Detects runaway reasoning loops in LLM agents using multiple
complementary detection strategies validated by academic research.

Detection layers:
    1. N-gram repetition (fast, pattern-based)
    2. Semantic similarity (embedding-based cosine distance)
    3. CUSUM drift (cumulative sum of embedding trajectory changes)
    4. Entropy/confidence monitoring (output distribution stability)
    5. Action/tool repetition (structural pattern matching)
    6. Compression similarity (NCD - information-theoretic, no embeddings)
    7. Edit distance decay (Mirror Loop metric - no embeddings)

References:
    - DeRep (Liu et al., 2025, arXiv:2504.12608): 20-pattern repetition
      taxonomy (originally for code generation, not reasoning loops)
    - Duan et al. (2026, arXiv:2601.05693): CUSUM-based loop detection + LoopBench dataset
    - TAAR (Chen et al., 2026, arXiv:2601.11940): Trap-aware adaptive restart
    - Conformal Thinking (Wang et al., 2026, arXiv:2602.03814): Statistical risk control
    - SMR (Lee et al., 2025, arXiv:2505.23059): State machine reasoning with Stop action
    - Kaiser et al. (2026, arXiv:2602.09805): Decomposing reasoning efficiency
    - Mirror Loop (DeVilling, 2025, arXiv:2510.21861): Edit distance decay as primary metric
    - REFRAIN (Sun et al., 2025, arXiv:2510.10103): Adaptive early-stopping for CoT
    - Reinforcement Inference (Sun, 2026, arXiv:2602.08520): Token entropy as control signal
    - GRU-Mem (Sheng et al., 2026, arXiv:2602.10560): RL-trained exit gates
    - Li et al. (2004, arXiv:cs/0111054): "The Similarity Metric" -- NCD theoretical basis
    - Cilibrasi & Vitányi (2005, arXiv:cs/0312044): "Clustering by Compression"
"""

from inferencebrake.types import (
    DetectionResult,
    DetectorVerdict,
    LoopType,
    SessionState,
    StepRecord,
    PipelineConfig,
    ThresholdConfig,
)
from inferencebrake.pipeline import DetectionPipeline
from inferencebrake.detectors import BaseDetector

__version__ = "0.1.0"
__all__ = [
    "DetectionPipeline",
    "DetectionResult",
    "DetectorVerdict",
    "LoopType",
    "SessionState",
    "StepRecord",
    "PipelineConfig",
    "ThresholdConfig",
    "BaseDetector",
]
