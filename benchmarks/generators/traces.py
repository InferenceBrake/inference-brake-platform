"""
Synthetic Trace Generators for Benchmarking.

Generates realistic agent reasoning traces with known ground-truth
labels for loop/no-loop classification. These are used to measure
detection accuracy, precision, recall, and latency.

Trace categories:
    1. LOOPING traces (positive class)
        - Exact repetition loops
        - Paraphrase loops (same idea, different words)
        - Action cycle loops (A->B->A->B)
        - Gradual drift loops (slowly converging)
        - Stalling loops (low-information padding)
    2. HEALTHY traces (negative class)
        - Progressive reasoning (clear forward progress)
        - Verbose but productive (lots of text, new info)
        - Legitimate revisiting (circling back with new context)
        - Code generation (naturally repetitive structure)
    3. ADVERSARIAL traces (hard cases)
        - Near-threshold similarity
        - Intermittent loops (loop, recover, loop again)
        - Long-content with buried loops
        - Mixed loop types in one session
"""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class GeneratedTrace:
    """A synthetic agent trace with ground truth labels."""

    trace_id: str
    category: str  # "looping", "healthy", "adversarial"
    subcategory: str  # e.g., "exact_repeat", "paraphrase", etc.
    steps: list[str]  # Reasoning text per step
    actions: list[list[str]]  # Action labels per step
    embeddings: list[list[float]]  # Synthetic embeddings per step
    labels: list[bool]  # Ground truth: True = loop at this step
    loop_onset_step: Optional[int]  # Step where loop begins (None if healthy)
    metadata: dict = field(default_factory=dict)

    @property
    def is_looping(self) -> bool:
        return any(self.labels)

    @property
    def total_steps(self) -> int:
        return len(self.steps)


def _random_embedding(dim: int = 384, seed: int | None = None) -> list[float]:
    """Generate a random unit vector of given dimension."""
    rng = np.random.RandomState(seed)
    vec = rng.randn(dim)
    vec = vec / np.linalg.norm(vec)
    return vec.tolist()


def _perturb_embedding(
    base: list[float], similarity: float, seed: int | None = None
) -> list[float]:
    """
    Generate an embedding with approximately the given cosine similarity
    to the base embedding.

    Uses the formula: new = base * sim + noise * sqrt(1 - sim^2)
    """
    rng = np.random.RandomState(seed)
    base_arr = np.asarray(base, dtype=np.float64)
    noise = rng.randn(len(base))
    # Make noise orthogonal to base
    noise = noise - np.dot(noise, base_arr) * base_arr
    noise = noise / max(np.linalg.norm(noise), 1e-10)
    # Combine
    new = base_arr * similarity + noise * math.sqrt(max(1.0 - similarity**2, 0.0))
    new = new / max(np.linalg.norm(new), 1e-10)
    return new.tolist()


def _make_id(category: str, idx: int) -> str:
    """Generate deterministic trace ID."""
    return f"trace_{category}_{idx:04d}"


# ============================================================
# LOOPING TRACE GENERATORS
# ============================================================

# Templates for reasoning steps
WEATHER_LOOP = [
    "I should check the weather for the user's location.",
    "Let me search for weather data in their area.",
    "I need to find weather information for this location.",
    "Let me look up the current weather conditions.",
    "I should get weather forecast data.",
    "Let me check what the weather is like there.",
    "I need to look at weather information.",
]

CODE_REFACTOR_LOOP = [
    "I should refactor this function to be more efficient.",
    "Let me improve the code structure of this method.",
    "I need to refactor this code for better performance.",
    "Let me restructure this function.",
    "I should optimize this method's implementation.",
    "Let me clean up this code.",
    "I need to improve the efficiency of this function.",
]

RESEARCH_LOOP = [
    "I need to analyze this data more carefully.",
    "Let me examine the evidence more closely.",
    "I should look at this from a different angle.",
    "Let me reconsider the available data.",
    "I need to re-examine the evidence.",
    "Let me take another look at the analysis.",
    "I should review the data once more.",
]

CONFIDENCE_LOOP = [
    "I'm fairly confident the answer is 42.",
    "Yes, I believe the answer is definitely 42.",
    "The answer is 42, I'm quite sure about this.",
    "After further consideration, the answer is 42.",
    "I can confirm that 42 is the correct answer.",
    "Having verified, the answer is indeed 42.",
    "The answer remains 42, as I determined.",
]

TOOL_CALL_LOOP_STEPS = [
    "Let me search the web for this information.",
    "I'll search the web again with different terms.",
    "Let me try another web search.",
    "I'll do one more web search to confirm.",
    "Let me search the web for more details.",
]

PROGRESSIVE_STEPS = [
    "The user wants to build a REST API. Let me identify the requirements.",
    "Based on the requirements, I'll choose FastAPI as the framework because it supports async and auto-generates docs.",
    "Now I'll design the data models. We need User, Product, and Order entities with proper relationships.",
    "Let me implement the database layer with SQLAlchemy ORM and migrations via Alembic.",
    "Now implementing the API endpoints: CRUD for users, products, and orders with proper validation.",
    "Adding authentication with JWT tokens. I'll use python-jose for token generation and bcrypt for password hashing.",
    "Finally, let me write integration tests using pytest and httpx for async endpoint testing.",
    "Adding error handling middleware, CORS configuration, and request logging for production readiness.",
]

VERBOSE_HEALTHY_STEPS = [
    (
        "I'll start by examining the database schema to understand the current structure. "
        "The schema has tables for users, products, and orders with foreign key relationships. "
        "The users table includes fields for email, password_hash, created_at, and role. "
        "This gives me a good foundation to work with."
    ),
    (
        "Now let me look at the existing API endpoints to see what's already implemented. "
        "I found GET /users, POST /users, GET /users/{id}, PUT /users/{id}. "
        "The products endpoints are: GET /products, POST /products with pagination. "
        "Missing: DELETE endpoints, batch operations, and filtering."
    ),
    (
        "For the new search feature, I need to add full-text search capability. "
        "PostgreSQL has built-in tsvector for this. I'll create a search index on "
        "product name and description fields. The search endpoint will accept query parameters "
        "for text search, category filter, price range, and sorting."
    ),
    (
        "Implementing the search endpoint now. Using PostgreSQL's to_tsvector and plainto_tsquery "
        "for the full-text search. Adding gin index for performance. The endpoint accepts "
        "q, category, min_price, max_price, sort_by, and limit parameters."
    ),
    (
        "Testing the search functionality. Query 'blue widget' returns 3 results. "
        "Category filter works correctly. Price range filtering verified. "
        "Pagination returns correct page sizes. Performance: 12ms average query time."
    ),
]

LEGITIMATE_REVISIT_STEPS = [
    "Let me first check the configuration file to understand the settings.",
    "Now I'll implement the core feature based on the config values I found.",
    "I need to go back to the config file - I realize I need the database connection settings too.",
    "Good, I have the DB settings now. Let me update the implementation to use connection pooling.",
    "Let me check the config one more time for the cache TTL values.",
    "Now I can complete the implementation with proper caching using the TTL from config.",
]

CODE_GENERATION_STEPS = [
    """def process_item(item: dict) -> dict:
    result = {}
    result['id'] = item.get('id')
    result['name'] = item.get('name', '').strip()
    result['price'] = float(item.get('price', 0))
    return result""",
    """def process_batch(items: list[dict]) -> list[dict]:
    results = []
    for item in items:
        processed = process_item(item)
        if processed['price'] > 0:
            results.append(processed)
    return results""",
    """def validate_item(item: dict) -> bool:
    required = ['id', 'name', 'price']
    for field in required:
        if field not in item:
            return False
    if not isinstance(item['price'], (int, float)):
        return False
    return True""",
    """def export_items(items: list[dict], format: str = 'json') -> str:
    validated = [i for i in items if validate_item(i)]
    processed = process_batch(validated)
    if format == 'json':
        return json.dumps(processed, indent=2)
    elif format == 'csv':
        return to_csv(processed)
    raise ValueError(f'Unknown format: {format}')""",
]


def generate_exact_repeat_traces(count: int, seed: int = 42) -> list[GeneratedTrace]:
    """Generate traces with exact text repetition."""
    rng = random.Random(seed)
    traces = []

    templates = [WEATHER_LOOP, CODE_REFACTOR_LOOP, RESEARCH_LOOP, CONFIDENCE_LOOP]

    for i in range(count):
        template = rng.choice(templates)
        num_steps = rng.randint(4, 8)
        loop_start = rng.randint(1, 3)

        steps = []
        labels = []
        embeddings = []
        base_emb = _random_embedding(seed=seed + i)

        for j in range(num_steps):
            if j < loop_start:
                # Pre-loop: use sequential steps
                step_text = template[j % len(template)]
                emb = _perturb_embedding(
                    base_emb, 0.3 + rng.random() * 0.3, seed=seed + i * 100 + j
                )
                labels.append(False)
            else:
                # Loop: repeat from a small pool
                pool = template[:3]
                step_text = pool[(j - loop_start) % len(pool)]
                # High similarity embeddings
                emb = _perturb_embedding(
                    base_emb, 0.88 + rng.random() * 0.10, seed=seed + i * 100 + j
                )
                labels.append(
                    j > loop_start
                )  # First repeat is onset, detect from second

            steps.append(step_text)
            embeddings.append(emb)

        traces.append(
            GeneratedTrace(
                trace_id=_make_id("exact_repeat", i),
                category="looping",
                subcategory="exact_repeat",
                steps=steps,
                actions=[[] for _ in steps],
                embeddings=embeddings,
                labels=labels,
                loop_onset_step=loop_start + 1,
            )
        )

    return traces


def generate_paraphrase_loop_traces(count: int, seed: int = 42) -> list[GeneratedTrace]:
    """Generate traces where the same idea is rephrased each time."""
    rng = random.Random(seed)
    traces = []

    for i in range(count):
        template = rng.choice([WEATHER_LOOP, CODE_REFACTOR_LOOP, RESEARCH_LOOP])
        num_steps = rng.randint(5, 10)
        loop_start = rng.randint(2, 4)

        steps = []
        labels = []
        embeddings = []
        base_emb = _random_embedding(seed=seed + i)

        for j in range(num_steps):
            if j < loop_start:
                step_text = template[j % len(template)]
                emb = _perturb_embedding(
                    base_emb, 0.3 + rng.random() * 0.3, seed=seed + i * 100 + j
                )
                labels.append(False)
            else:
                # Use different sentences but high semantic similarity
                step_text = template[(j - loop_start) % len(template)]
                # Paraphrases cluster tightly in embedding space (0.80-0.92)
                emb = _perturb_embedding(
                    base_emb, 0.82 + rng.random() * 0.10, seed=seed + i * 100 + j
                )
                labels.append(j > loop_start)

            steps.append(step_text)
            embeddings.append(emb)

        traces.append(
            GeneratedTrace(
                trace_id=_make_id("paraphrase", i),
                category="looping",
                subcategory="paraphrase",
                steps=steps,
                actions=[[] for _ in steps],
                embeddings=embeddings,
                labels=labels,
                loop_onset_step=loop_start + 1,
            )
        )

    return traces


def generate_action_loop_traces(count: int, seed: int = 42) -> list[GeneratedTrace]:
    """Generate traces with repeating tool/action patterns."""
    rng = random.Random(seed)
    traces = []

    action_patterns = [
        # Direct repeat
        (["search_web"] * 5, "direct_repeat"),
        # Short cycle
        (
            [
                "search_web",
                "parse_result",
                "search_web",
                "parse_result",
                "search_web",
                "parse_result",
            ],
            "short_cycle",
        ),
        # Long cycle
        (["search", "filter", "analyze", "search", "filter", "analyze"], "long_cycle"),
    ]

    for i in range(count):
        pattern_actions, subtype = rng.choice(action_patterns)
        num_steps = len(pattern_actions)
        loop_start = min(2, num_steps - 1)

        steps = []
        actions = []
        labels = []
        embeddings = []
        base_emb = _random_embedding(seed=seed + i)

        for j in range(num_steps):
            step_text = f"Executing action: {pattern_actions[j]}. Step {j + 1}."
            steps.append(step_text)
            actions.append([pattern_actions[j]])
            emb = _perturb_embedding(
                base_emb, 0.5 + rng.random() * 0.3, seed=seed + i * 100 + j
            )
            embeddings.append(emb)
            labels.append(j >= loop_start + 2)

        traces.append(
            GeneratedTrace(
                trace_id=_make_id("action_loop", i),
                category="looping",
                subcategory=f"action_{subtype}",
                steps=steps,
                actions=actions,
                embeddings=embeddings,
                labels=labels,
                loop_onset_step=loop_start + 2,
            )
        )

    return traces


def generate_gradual_drift_traces(count: int, seed: int = 42) -> list[GeneratedTrace]:
    """Generate traces that slowly converge (drift toward repetition)."""
    rng = random.Random(seed)
    traces = []

    for i in range(count):
        num_steps = rng.randint(8, 15)
        base_emb = _random_embedding(seed=seed + i)

        steps = []
        labels = []
        embeddings = []
        # Start with low similarity, gradually increase
        for j in range(num_steps):
            # Similarity increases linearly from 0.3 to 0.95
            progress = j / (num_steps - 1)
            target_sim = 0.3 + progress * 0.65
            emb = _perturb_embedding(base_emb, target_sim, seed=seed + i * 100 + j)
            embeddings.append(emb)
            step_text = f"Step {j + 1}: Analyzing the problem from angle {j + 1}. " + (
                "Making good progress."
                if j < num_steps // 2
                else "Revisiting earlier analysis."
            )
            steps.append(step_text)
            labels.append(target_sim >= 0.85)

        loop_onset = next(
            (j for j in range(num_steps) if 0.3 + j / (num_steps - 1) * 0.65 >= 0.85),
            None,
        )

        traces.append(
            GeneratedTrace(
                trace_id=_make_id("gradual_drift", i),
                category="looping",
                subcategory="gradual_drift",
                steps=steps,
                actions=[[] for _ in steps],
                embeddings=embeddings,
                labels=labels,
                loop_onset_step=loop_onset,
            )
        )

    return traces


def generate_stalling_traces(count: int, seed: int = 42) -> list[GeneratedTrace]:
    """Generate traces where the agent stalls with low-information content."""
    rng = random.Random(seed)
    traces = []

    stalling_phrases = [
        "Let me think about this more carefully.",
        "I need to consider all the options here.",
        "This is a complex problem that requires careful analysis.",
        "I should think about this step by step.",
        "Let me reconsider my approach.",
        "I want to make sure I get this right.",
        "This deserves more careful thought.",
        "I need to weigh all the factors.",
    ]

    for i in range(count):
        num_steps = rng.randint(5, 9)
        stall_start = rng.randint(2, 3)

        steps = []
        labels = []
        embeddings = []
        base_emb = _random_embedding(seed=seed + i)

        for j in range(num_steps):
            if j < stall_start:
                step_text = f"Step {j + 1}: Making concrete progress on the task. Found relevant data point {j + 1}."
                emb = _perturb_embedding(
                    base_emb, 0.3 + rng.random() * 0.2, seed=seed + i * 100 + j
                )
                labels.append(False)
            else:
                step_text = rng.choice(stalling_phrases)
                emb = _perturb_embedding(
                    base_emb, 0.85 + rng.random() * 0.10, seed=seed + i * 100 + j
                )
                labels.append(j > stall_start)

            steps.append(step_text)
            embeddings.append(emb)

        traces.append(
            GeneratedTrace(
                trace_id=_make_id("stalling", i),
                category="looping",
                subcategory="stalling",
                steps=steps,
                actions=[[] for _ in steps],
                embeddings=embeddings,
                labels=labels,
                loop_onset_step=stall_start + 1,
            )
        )

    return traces


# ============================================================
# HEALTHY TRACE GENERATORS
# ============================================================


def generate_progressive_traces(count: int, seed: int = 42) -> list[GeneratedTrace]:
    """Generate traces with clear forward progress (no loops)."""
    rng = random.Random(seed)
    traces = []

    for i in range(count):
        num_steps = rng.randint(4, len(PROGRESSIVE_STEPS))
        steps = PROGRESSIVE_STEPS[:num_steps]

        embeddings = []
        base_emb = _random_embedding(seed=seed + i)
        for j in range(num_steps):
            # Low similarity between steps - each step is distinct
            emb = _perturb_embedding(
                base_emb, 0.2 + rng.random() * 0.3, seed=seed + i * 100 + j
            )
            embeddings.append(emb)
            # Shift base for each step to ensure diversity
            base_emb = emb

        traces.append(
            GeneratedTrace(
                trace_id=_make_id("progressive", i),
                category="healthy",
                subcategory="progressive",
                steps=steps,
                actions=[
                    ["analyze", "implement", "test"][j % 3 : j % 3 + 1]
                    for j in range(num_steps)
                ],
                embeddings=embeddings,
                labels=[False] * num_steps,
                loop_onset_step=None,
            )
        )

    return traces


def generate_verbose_healthy_traces(count: int, seed: int = 42) -> list[GeneratedTrace]:
    """Generate verbose but productive traces (lots of text, but new info)."""
    rng = random.Random(seed)
    traces = []

    for i in range(count):
        steps = list(VERBOSE_HEALTHY_STEPS)
        num_steps = len(steps)

        embeddings = []
        base_emb = _random_embedding(seed=seed + i)
        for j in range(num_steps):
            emb = _perturb_embedding(
                base_emb, 0.3 + rng.random() * 0.25, seed=seed + i * 100 + j
            )
            embeddings.append(emb)
            base_emb = emb

        traces.append(
            GeneratedTrace(
                trace_id=_make_id("verbose_healthy", i),
                category="healthy",
                subcategory="verbose_healthy",
                steps=steps,
                actions=[[] for _ in steps],
                embeddings=embeddings,
                labels=[False] * num_steps,
                loop_onset_step=None,
            )
        )

    return traces


def generate_legitimate_revisit_traces(
    count: int, seed: int = 42
) -> list[GeneratedTrace]:
    """Generate traces that revisit earlier topics but with new context."""
    rng = random.Random(seed)
    traces = []

    for i in range(count):
        steps = list(LEGITIMATE_REVISIT_STEPS)
        num_steps = len(steps)

        embeddings = []
        base_emb = _random_embedding(seed=seed + i)
        for j in range(num_steps):
            # Steps 2 and 4 revisit config - moderate similarity to steps 0 and 2
            if j in (2, 4):
                # Similar to earlier step but not identical
                ref_emb = embeddings[0] if j == 2 else embeddings[2]
                emb = _perturb_embedding(
                    ref_emb, 0.65 + rng.random() * 0.10, seed=seed + i * 100 + j
                )
            else:
                emb = _perturb_embedding(
                    base_emb, 0.3 + rng.random() * 0.2, seed=seed + i * 100 + j
                )
                base_emb = emb
            embeddings.append(emb)

        traces.append(
            GeneratedTrace(
                trace_id=_make_id("revisit", i),
                category="healthy",
                subcategory="legitimate_revisit",
                steps=steps,
                actions=[[] for _ in steps],
                embeddings=embeddings,
                labels=[False] * num_steps,
                loop_onset_step=None,
            )
        )

    return traces


def generate_code_generation_traces(count: int, seed: int = 42) -> list[GeneratedTrace]:
    """Generate code generation traces (naturally repetitive structure)."""
    rng = random.Random(seed)
    traces = []

    for i in range(count):
        steps = list(CODE_GENERATION_STEPS)
        num_steps = len(steps)

        embeddings = []
        base_emb = _random_embedding(seed=seed + i)
        for j in range(num_steps):
            # Code has moderate structural similarity but different content
            emb = _perturb_embedding(
                base_emb, 0.50 + rng.random() * 0.20, seed=seed + i * 100 + j
            )
            embeddings.append(emb)

        traces.append(
            GeneratedTrace(
                trace_id=_make_id("code_gen", i),
                category="healthy",
                subcategory="code_generation",
                steps=steps,
                actions=[["write_code"] for _ in steps],
                embeddings=embeddings,
                labels=[False] * num_steps,
                loop_onset_step=None,
            )
        )

    return traces


# ============================================================
# ADVERSARIAL TRACE GENERATORS
# ============================================================


def generate_near_threshold_traces(count: int, seed: int = 42) -> list[GeneratedTrace]:
    """Generate traces with similarity just below/above threshold."""
    rng = random.Random(seed)
    traces = []

    for i in range(count):
        num_steps = rng.randint(5, 8)
        is_loop = i % 2 == 0  # Alternate: half are loops, half aren't

        steps = []
        labels = []
        embeddings = []
        base_emb = _random_embedding(seed=seed + i)

        for j in range(num_steps):
            if is_loop:
                # Just above threshold: 0.85-0.88
                target_sim = 0.85 + rng.random() * 0.03
                labels.append(j >= 2)
            else:
                # Just below threshold: 0.80-0.84
                target_sim = 0.80 + rng.random() * 0.04
                labels.append(False)

            emb = _perturb_embedding(base_emb, target_sim, seed=seed + i * 100 + j)
            embeddings.append(emb)
            steps.append(
                f"Near-threshold step {j + 1}. Similarity target: ~{target_sim:.2f}"
            )

        traces.append(
            GeneratedTrace(
                trace_id=_make_id("near_threshold", i),
                category="adversarial",
                subcategory="near_threshold_loop"
                if is_loop
                else "near_threshold_healthy",
                steps=steps,
                actions=[[] for _ in steps],
                embeddings=embeddings,
                labels=labels,
                loop_onset_step=2 if is_loop else None,
                metadata={"is_loop_gt": is_loop},
            )
        )

    return traces


def generate_intermittent_loop_traces(
    count: int, seed: int = 42
) -> list[GeneratedTrace]:
    """Generate traces that loop, recover, then loop again."""
    rng = random.Random(seed)
    traces = []

    for i in range(count):
        num_steps = rng.randint(10, 15)
        steps = []
        labels = []
        embeddings = []
        base_emb = _random_embedding(seed=seed + i)

        phase = "healthy"  # healthy -> looping -> healthy -> looping
        phase_counter = 0
        phase_lengths = [3, 3, 2, 4]  # steps per phase
        phase_idx = 0

        for j in range(num_steps):
            current_phase_len = (
                phase_lengths[phase_idx] if phase_idx < len(phase_lengths) else 3
            )
            if phase_counter >= current_phase_len:
                phase_idx += 1
                phase = "looping" if phase == "healthy" else "healthy"
                phase_counter = 0

            if phase == "healthy":
                emb = _perturb_embedding(
                    base_emb, 0.3 + rng.random() * 0.2, seed=seed + i * 100 + j
                )
                base_emb = emb
                labels.append(False)
                step_text = f"Making progress on step {j + 1}."
            else:
                emb = _perturb_embedding(
                    base_emb, 0.87 + rng.random() * 0.08, seed=seed + i * 100 + j
                )
                labels.append(True)
                step_text = f"Reconsidering the problem from step {j + 1}."

            steps.append(step_text)
            embeddings.append(emb)
            phase_counter += 1

        traces.append(
            GeneratedTrace(
                trace_id=_make_id("intermittent", i),
                category="adversarial",
                subcategory="intermittent",
                steps=steps,
                actions=[[] for _ in steps],
                embeddings=embeddings,
                labels=labels,
                loop_onset_step=3,  # First loop phase
            )
        )

    return traces


def generate_long_content_traces(count: int, seed: int = 42) -> list[GeneratedTrace]:
    """Generate traces with very long reasoning text (stress test)."""
    rng = random.Random(seed)
    traces = []

    for i in range(count):
        num_steps = rng.randint(5, 8)
        is_loop = i % 2 == 0

        steps = []
        labels = []
        embeddings = []
        base_emb = _random_embedding(seed=seed + i)

        for j in range(num_steps):
            # Generate long text (1000-5000 words)
            word_count = rng.randint(1000, 5000)
            words = [f"word_{rng.randint(0, 500)}" for _ in range(word_count)]

            if is_loop and j >= 3:
                # Bury the loop in long text - repeat earlier key phrases
                words[-200:] = words[:200]  # Copy beginning to end
                emb = _perturb_embedding(
                    base_emb, 0.88 + rng.random() * 0.08, seed=seed + i * 100 + j
                )
                labels.append(j > 3)
            else:
                emb = _perturb_embedding(
                    base_emb, 0.3 + rng.random() * 0.3, seed=seed + i * 100 + j
                )
                labels.append(False)
                base_emb = emb

            steps.append(" ".join(words))
            embeddings.append(emb)

        traces.append(
            GeneratedTrace(
                trace_id=_make_id("long_content", i),
                category="adversarial",
                subcategory="long_content_loop" if is_loop else "long_content_healthy",
                steps=steps,
                actions=[[] for _ in steps],
                embeddings=embeddings,
                labels=labels,
                loop_onset_step=4 if is_loop else None,
                metadata={
                    "avg_word_count": sum(len(s.split()) for s in steps) / len(steps)
                },
            )
        )

    return traces


# ============================================================
# MASTER GENERATOR
# ============================================================


def generate_benchmark_dataset(
    traces_per_category: int = 50,
    seed: int = 42,
) -> list[GeneratedTrace]:
    """
    Generate a complete benchmark dataset with balanced classes.

    Returns traces from all categories:
        - Looping (5 subcategories x traces_per_category)
        - Healthy (4 subcategories x traces_per_category)
        - Adversarial (3 subcategories x traces_per_category)

    Total: 12 * traces_per_category traces
    """
    all_traces = []

    # Looping traces (positive class)
    all_traces.extend(generate_exact_repeat_traces(traces_per_category, seed))
    all_traces.extend(generate_paraphrase_loop_traces(traces_per_category, seed + 1000))
    all_traces.extend(generate_action_loop_traces(traces_per_category, seed + 2000))
    all_traces.extend(generate_gradual_drift_traces(traces_per_category, seed + 3000))
    all_traces.extend(generate_stalling_traces(traces_per_category, seed + 4000))

    # Healthy traces (negative class)
    all_traces.extend(generate_progressive_traces(traces_per_category, seed + 5000))
    all_traces.extend(generate_verbose_healthy_traces(traces_per_category, seed + 6000))
    all_traces.extend(
        generate_legitimate_revisit_traces(traces_per_category, seed + 7000)
    )
    all_traces.extend(generate_code_generation_traces(traces_per_category, seed + 8000))

    # Adversarial traces (hard cases)
    all_traces.extend(generate_near_threshold_traces(traces_per_category, seed + 9000))
    all_traces.extend(
        generate_intermittent_loop_traces(traces_per_category, seed + 10000)
    )
    all_traces.extend(generate_long_content_traces(traces_per_category, seed + 11000))

    return all_traces
