# benchmark_format.py

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class LoopType(Enum):
    """Types of loops that can be detected"""

    NONE = "none"
    SEMANTIC = "semantic"  # Repeated similar reasoning
    ACTION = "action"  # Repeated actions/tool calls
    NAVIGATION = "navigation"  # Repeated URL visits (WebArena)
    CONFIDENCE = "confidence"  # High confidence without progress
    REFACTORING = "refactoring"  # Code refactoring loops (SWE-bench)
    CUSUM = "cusum"  # CUSUM stagnation detection
    NGRAM = "ngram"  # N-gram repetition
    ENTROPY = "entropy"  # Entropy collapse


@dataclass
class BenchmarkStep:
    """Single step in an agent trace"""

    reasoning: str  # Agent's thought/reasoning
    action: Optional[str] = None  # Action taken (tool call, click, etc)
    observation: Optional[str] = None  # Result/feedback from action
    step_number: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkTrace:
    """
    Standardized format for benchmark data
    Compatible with all data sources:
    - TRAIL: Debug agent errors, hallucination detection
    - Agent Reward Bench: Quality-labeled agent trajectories
    - WebArena-Verified: Reliable web agent interactions
    - SWE-bench-Verified: Verified coding agent tasks
    - Synthetic: Generated loop patterns
    """

    id: str
    source: str  # 'trail', 'agent_reward_bench', 'webarena_verified', 'swebench_verified', 'synthetic'
    steps: List[BenchmarkStep]

    # Labels (for evaluation)
    label: Optional[str] = None  # 'loop' or 'no_loop'
    loop_type: Optional[LoopType] = None

    # Task info
    success: Optional[bool] = None  # Did the agent complete the task?
    task: Optional[str] = None  # Task description

    # Quality metrics (from Agent Reward Bench)
    reward: Optional[float] = None
    quality: Optional[str] = None  # 'high', 'medium', 'low'

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "source": self.source,
            "steps": [
                {
                    "reasoning": s.reasoning,
                    "action": s.action,
                    "observation": s.observation,
                    "step_number": s.step_number,
                    "metadata": s.metadata,
                }
                for s in self.steps
            ],
            "label": self.label,
            "loop_type": self.loop_type.value if self.loop_type else None,
            "success": self.success,
            "task": self.task,
            "reward": self.reward,
            "quality": self.quality,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BenchmarkTrace":
        """Load from dictionary"""
        steps = [
            BenchmarkStep(
                reasoning=s["reasoning"],
                action=s.get("action"),
                observation=s.get("observation"),
                step_number=s.get("step_number", i),
                metadata=s.get("metadata", {}),
            )
            for i, s in enumerate(data["steps"])
        ]

        loop_type = None
        if data.get("loop_type"):
            loop_type = LoopType(data["loop_type"])

        return cls(
            id=data["id"],
            source=data["source"],
            steps=steps,
            label=data.get("label"),
            loop_type=loop_type,
            success=data.get("success"),
            task=data.get("task"),
            reward=data.get("reward"),
            quality=data.get("quality"),
            metadata=data.get("metadata", {}),
        )


# Conversion functions for each data source
def standardize_trail(raw_data: dict) -> BenchmarkTrace:
    """Convert TRAIL format to BenchmarkTrace"""
    return BenchmarkTrace(
        id=raw_data["id"],
        source="trail",
        steps=[
            BenchmarkStep(
                reasoning=raw_data["steps"][0]["reasoning"],
                action=None,
                observation=None,
                step_number=0,
            )
        ],
        success=not raw_data.get("has_hallucination", False),
        label="loop"
        if raw_data.get("has_hallucination")
        else None,  # Hallucination correlates with loops
        metadata={
            "query": raw_data.get("query", ""),
            "domain": raw_data["metadata"].get("domain", "unknown"),
        },
    )


def standardize_agent_reward_bench(raw_data: dict) -> BenchmarkTrace:
    """Convert Agent Reward Bench format to BenchmarkTrace"""
    steps = [
        BenchmarkStep(
            reasoning=s["reasoning"],
            action=s.get("action"),
            observation=s.get("observation"),
            step_number=i,
        )
        for i, s in enumerate(raw_data["steps"])
    ]

    return BenchmarkTrace(
        id=raw_data["id"],
        source="agent_reward_bench",
        steps=steps,
        success=raw_data.get("success", False),
        reward=raw_data.get("reward"),
        quality=raw_data["metadata"].get("quality"),
        task=raw_data["metadata"].get("task"),
        # Label based on reward: low reward often indicates loops
        label="loop" if raw_data.get("reward", 0) < 0.3 else None,
        metadata=raw_data.get("metadata", {}),
    )


def standardize_webarena_verified(raw_data: dict) -> BenchmarkTrace:
    """Convert WebArena-Verified format to BenchmarkTrace"""
    steps = [
        BenchmarkStep(
            reasoning=s["reasoning"],
            action=s.get("action"),
            observation=s.get("observation"),
            step_number=i,
        )
        for i, s in enumerate(raw_data["steps"])
    ]

    # Detect navigation loops
    has_repeated_actions = raw_data["metadata"].get("has_repeated_actions", False)

    return BenchmarkTrace(
        id=raw_data["id"],
        source="webarena_verified",
        steps=steps,
        success=raw_data.get("success", False),
        task=raw_data.get("task"),
        label="loop" if has_repeated_actions else None,
        loop_type=LoopType.NAVIGATION if has_repeated_actions else None,
        metadata=raw_data.get("metadata", {}),
    )


def standardize_swebench_verified(raw_data: dict) -> BenchmarkTrace:
    """Convert SWE-bench-Verified format to BenchmarkTrace"""
    steps = [
        BenchmarkStep(
            reasoning=s["reasoning"],
            action=s.get("action"),
            observation=s.get("observation"),
            step_number=i,
        )
        for i, s in enumerate(raw_data["steps"])
    ]

    return BenchmarkTrace(
        id=raw_data["id"],
        source="swebench_verified",
        steps=steps,
        success=raw_data.get("success", False),
        task=raw_data.get("problem_statement"),
        # Failed tasks with many steps might be loops
        label="loop" if not raw_data.get("success") and len(steps) > 5 else None,
        loop_type=LoopType.REFACTORING if not raw_data.get("success") else None,
        metadata={
            "repo": raw_data["metadata"].get("repo"),
            "patch": raw_data.get("patch", "")[:500],  # Truncate
        },
    )


def standardize_synthetic(raw_data: dict) -> BenchmarkTrace:
    """Convert synthetic format to BenchmarkTrace"""
    steps = [
        BenchmarkStep(
            reasoning=s["reasoning"],
            action=s.get("action"),
            observation=s.get("observation"),
            step_number=i,
        )
        for i, s in enumerate(raw_data["steps"])
    ]

    loop_type = None
    if raw_data.get("loop_type"):
        loop_type = LoopType(raw_data["loop_type"])

    return BenchmarkTrace(
        id=raw_data["id"],
        source="synthetic",
        steps=steps,
        label=raw_data["label"],
        loop_type=loop_type,
        success=raw_data["label"] != "loop",
        metadata=raw_data.get("metadata", {}),
    )


# Main standardization function
def standardize_trace(raw_data: dict) -> Optional[BenchmarkTrace]:
    """
    Convert any format to standardized BenchmarkTrace
    """
    source = raw_data.get("source")

    if source == "trail":
        return standardize_trail(raw_data)
    elif source == "agent_reward_bench":
        return standardize_agent_reward_bench(raw_data)
    elif source == "webarena_verified":
        return standardize_webarena_verified(raw_data)
    elif source == "swebench_verified":
        return standardize_swebench_verified(raw_data)
    elif source == "synthetic":
        return standardize_synthetic(raw_data)
    else:
        print(f"Warning: Unknown source '{source}'")
        return None
