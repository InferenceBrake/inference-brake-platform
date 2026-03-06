# InferenceBrake - Research References

All papers that informed the detector designs and benchmark methodology.

---

## Core Loop Detection Papers

### Mirror Loop

**The Mirror Loop: Recursive Non-Convergence in Generative Reasoning Systems**  
Bentley DeVilling (Course Correct Labs), 2025  
<https://arxiv.org/abs/2510.21861>

> Primary basis for the **Edit Distance Decay** detector. Introduces the delta_I metric (normalised edit distance between consecutive steps). Found a 55% decline in informational change (0.193 → 0.087) across ungrounded runs, consistent across GPT-4o-mini, Claude 3 Haiku, and Gemini 2.0 Flash. A single grounding intervention at step 3 causes a +28% rebound.

---

### Circular Reasoning / LoopBench

**Circular Reasoning: Understanding Self-Reinforcing Loops in Large Reasoning Models**  
Zenghao Duan, Liang Pang, Zihao Wei, Wenbin Duan et al., January 2026  
<https://arxiv.org/abs/2601.05693>

> The most direct academic precedent for the **CUSUM** detector. Uses the CUSUM algorithm to monitor hidden-state shifts that precede textual repetition in Large Reasoning Models. Key finding: semantic repetition consistently precedes textual repetition, meaning trajectory-based detection catches loops earlier than similarity thresholds alone. Introduces **LoopBench**, a dataset with two loop typologies: *numerical loops* and *statement loops*.
>
> LoopBench availability: Not yet publicly released. Could add to `collect_benchmark_data.py` when released - it would be the only benchmark designed *specifically* for reasoning loop detection with ground-truth loop labels.

---

### TAAR

**Thinking Traps in Long Chain-of-Thought: A Measurable Study and Trap-Aware Adaptive Restart**  
Kang Chen et al., January 2026  
<https://arxiv.org/abs/2601.11940>

> Key reference for the **CUSUM** and **Semantic** detectors. Finds that 89% of Long-CoT failures exhibit prefix-dominant deadlocks, motivating trajectory-based (rather than point-in-time) detection.

---

### REFRAIN

**Stop When Enough: Adaptive Early-Stopping for Chain-of-Thought Reasoning**  
Renliang Sun, Wei Cheng, Dawei Li, Haifeng Chen, Wei Wang, October 2025  
<https://arxiv.org/abs/2510.10103>

> Informs the **Edit Distance** and **Entropy** detectors. Sliding-window reflective redundancy detection as a principled stopping criterion for CoT.

---

### DeRep

**Code Copycat Conundrum: Demystifying Repetition in LLM-based Code Generation**  
Mingwei Liu et al., April 2025  
<https://arxiv.org/abs/2504.12608>

> Basis for the **N-gram** detector's pattern taxonomy. Note: this paper studies repetition in *code generation* specifically, not agent reasoning loops. The 20-pattern taxonomy (rep-line, sim-line, rep-char, block repetition, structural repetition) transfers well conceptually, but the paper's accuracy claims (91%+) apply to code, not reasoning traces.

---

### SMR

**From Token to Action: State Machine Reasoning to Mitigate Overthinking in Information Retrieval**  
Dohyeon Lee, Yeonseok Jeong, Seung-won Hwang, May 2025  
<https://arxiv.org/abs/2505.23059>

> Basis for the **Action** detector. Models agent reasoning as a state machine with explicit `{Refine, Rerank, Stop}` transitions. Achieves 74.4% token reduction by detecting when an agent should stop vs. continue iterating.

---

## Supporting / Secondary References

### Reinforcement Inference

**Reinforcement Inference: Leveraging Uncertainty for Self-Correcting Language Model Reasoning**  
Xinhai Sun, 2026  
<https://arxiv.org/abs/2602.08520>

> Informs the Entropy detector. Proposes token-level entropy as a control signal - high entropy triggers re-attempt. Reports 60.72% to 84.03% accuracy improvement.

---

### Conformal Thinking

**Conformal Thinking: Risk Control for Reasoning on a Compute Budget**  
Xi Wang et al., February 2026  
<https://arxiv.org/abs/2602.03814>

> Secondary reference for the **Entropy** detector. Distribution-free statistical risk control for reasoning budgets; motivates preemptive stopping on unsolvable instances.

---

### Kaiser et al

**Decomposing Reasoning Efficiency in Large Language Models**  
Daniel Kaiser et al., February 2026  
<https://arxiv.org/abs/2602.09805>

> Informs threshold calibration in `types.py`. Develops deterministic trace-quality measures (grounding, repetition, prompt-copying) that separate degenerate looping from verbose-but-engaged reasoning. Used to justify per-task-type threshold adjustments.

---

### GRU-Mem

**When to Memorize and When to Stop: Gated Recurrent Memory for Long-Context Reasoning**  
Leheng Sheng et al., February 2026  
<https://arxiv.org/abs/2602.10560>

> Secondary reference for the **Action** detector. RL-trained exit gates that only update memory on new evidence and exit when sufficient evidence has been collected.

---

## Foundational / Classical References

### NCD - The Similarity Metric

**The Similarity Metric**  
Ming Li, Xin Chen, Xin Li, Bin Ma, Paul Vitányi, 2004  
*IEEE Transactions on Information Theory*  
<https://arxiv.org/abs/cs/0111054>

> Theoretical foundation for the **Compression (NCD)** detector. Derives the Normalized Compression Distance from Kolmogorov complexity as a universal similarity measure.

---

### Clustering by Compression

**Clustering by Compression**  
Rudi Cilibrasi, Paul Vitányi, 2005  
*IEEE Transactions on Information Theory*  
<https://arxiv.org/abs/cs/0312044>

> Companion to Li et al. (2004). Demonstrates practical applications of NCD using standard compressors (zlib, gzip) as approximations of Kolmogorov complexity.

---

### Information Distance

**Information Distance**  
Charles H. Bennett, Péter Gács, Ming Li, Paul Vitányi, Wojciech Zurek, 1998  
*SIAM Journal on Computing*

> Theoretical basis for information distance; predates arXiv availability. No link available.

---

### CUSUM

**Continuous Inspection Schemes**  
E. S. Page, 1954  
*Biometrika, 41(1/2), 100-115*

> The original CUSUM (cumulative sum) change-point detection algorithm used in the CUSUM Drift detector. No link available - predates digital archives.

---

## Benchmark Datasets

| Dataset | Use | Link |
|---|---|---|
| PatronusAI/TRAIL | Agent debug traces, filtered to >=5 steps, treated as healthy | <https://huggingface.co/datasets/PatronusAI/TRAIL> |
| generators/traces.py | Balanced synthetic traces with pre-computed embeddings | Local: `benchmarks/generators/traces.py` |
| synthetic templates | Additional loop traces for text-only detectors | Generated by `collect_benchmark_data.py` |

### Not Used

- **princeton-nlp/SWE-bench_Verified**: Synthetic boilerplate, no real agent traces, null labels
- **McGill-NLP/agent-reward-bench**: Eval metadata only - not used for loop detection
- **AmineHA/WebArena-Verified**: Task definitions only - not used for loop detection

---

## Removed References

### ~~Healy et al. (2026, arXiv:2601.05214)~~

*Internal Representations as Indicators of Hallucinations in Agent Tool Selection*

Removed. This paper is about tool-calling hallucination detection via hidden-state probes, not reasoning loop detection. The connection to CUSUM was only analogical and did not justify inclusion as a primary reference.
