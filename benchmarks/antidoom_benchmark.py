"""Antidoom benchmark: measure the token-repeat detector on real model completions.

Prompts come from LiquidAI/antidoom-mix-v1.0, a prompt-only mixture built to
elicit doom loops. Each prompt is completed by a model at low temperature, then
scored two ways:

  1. Ground truth: the largest n for which some n-gram of tokens repeats, computed
     independently with a sliding n-gram counter. A completion is "severe" when
     that span is >= SEVERE_SPAN (16) tokens.
  2. Detector: the hosted InferenceBrake check API (token_repeat votes at 6
     tokens) and the engine's TokenRepeatDetector, for comparison.

Because ground truth uses a much stricter threshold than the detector, the
comparison measures specificity: how often the 6-token threshold fires on
completions that are not severely degenerate.

Env:
    OPENROUTER_API_KEY       required
    INFERENCEBRAKE_API_KEY   required
    OPENROUTER_MODEL         optional, default deepseek/deepseek-v4-flash-0731:free

Run (from the repo root, using the engine venv):
    uv run --project packages/engine python benchmarks/antidoom_benchmark.py --limit 30
"""

import argparse
import json
import os
import re
import statistics
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import requests

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
IB_BASE = os.getenv("INFERENCEBRAKE_URL", "https://ocnjiyiqeifllbyqohks.supabase.co")
IB_CHECK_URL = f"{IB_BASE}/functions/v1/check"
SEVERE_SPAN = 16
DETECTOR_SPAN = 6
SWEEP_SPANS = [6, 8, 10, 12, 16]

# Prompts that reliably drive a model into verbatim repetition, used to obtain
# positive examples alongside the dataset prompts (which are mostly negatives).
INDUCED_PROMPTS = [
    "Write the sentence 'the agent keeps retrying the same call' over and over for 400 words.",
    "Write the paragraph 'The service is unavailable. I will retry.' over and over for 300 words.",
    "Count from 1 to 30, then continue repeating the final number for another 300 words.",
    "Write the phrase 'I need to check the weather in New York City' repeatedly for 400 words.",
    "Keep outputting the line 'Let me call the weather API again.' until you reach 350 words.",
]

WORD_RE = re.compile(r"[a-z0-9']+")


def tokenize(text):
    return WORD_RE.findall((text or "").lower())


def longest_repeated_ngram(tokens, max_n=40):
    """Largest n with a repeated n-gram. Independent of the detector's DP."""
    if len(tokens) < 2:
        return 0
    upper = min(max_n, len(tokens) // 2)
    for n in range(upper, 0, -1):
        counts = Counter(tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1))
        if any(c >= 2 for c in counts.values()):
            return n
    return 0


def load_prompts(limit, induce=0):
    from datasets import load_dataset

    ds = load_dataset("LiquidAI/antidoom-mix-v1.0", split="train", streaming=True)
    prompts = []
    for row in ds:
        conversations = row.get("conversations") or []
        humans = [c.get("value", "") for c in conversations if c.get("from") == "human"]
        if humans and humans[0].strip():
            prompts.append(humans[0].strip())
        if len(prompts) >= limit:
            break
    for i in range(induce):
        prompts.append(INDUCED_PROMPTS[i % len(INDUCED_PROMPTS)])
    return prompts


def generate(prompt, model, api_key, max_tokens, temperature, retries=4):
    """Generate one completion, retrying transient provider errors."""
    last = None
    for attempt in range(retries):
        try:
            resp = requests.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://inferencebrake.dev",
                    "X-Title": "InferenceBrake antidoom benchmark",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=180,
            )
        except requests.exceptions.RequestException as e:
            last = str(e)
            time.sleep(3 * (attempt + 1))
            continue

        if resp.status_code == 200:
            choices = resp.json().get("choices") or []
            if choices:
                return choices[0].get("message", {}).get("content") or ""

        last = f"{resp.status_code}: {resp.text[:200]}"
        if resp.status_code in (429, 500, 502, 503, 504):
            time.sleep(3 * (attempt + 1))
            continue
        break
    raise RuntimeError(f"OpenRouter generation failed ({last})")


def check_api(reasoning, session_id, api_key):
    resp = requests.post(
        IB_CHECK_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"session_id": session_id, "reasoning": reasoning},
        timeout=30,
    )
    if resp.status_code != 200:
        return None
    return resp.json()


def engine_vote(reasoning):
    try:
        from inferencebrake.detectors.token_repeat import TokenRepeatDetector
        from inferencebrake.types import DetectorVerdict, SessionState, ThresholdConfig

        detector = TokenRepeatDetector()
        session = SessionState(session_id="bench")
        signal = detector.detect(reasoning, session, ThresholdConfig())

        votes = {}
        for threshold in SWEEP_SPANS:
            config = ThresholdConfig()
            config.token_repeat_min_span = threshold
            config.token_repeat_warn_span = max(1, threshold - 2)
            sweep_signal = detector.detect(reasoning, session, config)
            votes[str(threshold)] = sweep_signal.verdict == DetectorVerdict.LOOP_DETECTED

        return (
            signal.verdict == DetectorVerdict.LOOP_DETECTED,
            signal.metadata.get("span_len", 0),
            votes,
        )
    except Exception:  # pragma: no cover
        return None, 0, {}


def ratio(num, den):
    return round(num / den, 4) if den else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--induce", type=int, default=0, help="number of repetition-inducing prompts to add")
    parser.add_argument("--model", default=os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free"))
    parser.add_argument("--max-tokens", type=int, default=400)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--session", default=f"antidoom-{int(time.time())}")
    args = parser.parse_args()

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    ib_key = os.getenv("INFERENCEBRAKE_API_KEY")
    if not openrouter_key or not ib_key:
        sys.exit("Set OPENROUTER_API_KEY and INFERENCEBRAKE_API_KEY")

    print(f"model={args.model} limit={args.limit} severe>={SEVERE_SPAN} detector>={DETECTOR_SPAN}\n")

    prompts = load_prompts(args.limit, args.induce)
    print(f"loaded {len(prompts)} prompts ({args.limit} dataset + {args.induce} induced)\n")

    rows = []
    for i, prompt in enumerate(prompts, 1):
        try:
            completion = generate(prompt, args.model, openrouter_key, args.max_tokens, args.temperature)
        except Exception as e:
            print(f"[{i}] generation failed: {e}")
            continue

        tokens = tokenize(completion)
        gt_span = longest_repeated_ngram(tokens)
        severe = gt_span >= SEVERE_SPAN

        api = check_api(completion, args.session, ib_key)
        api_vote = bool(api and api.get("detectors", {}).get("token_repeat"))
        api_conf = (api or {}).get("confidence", 0.0)

        eng_vote, eng_span, eng_votes = engine_vote(completion)

        rows.append({
            "prompt": prompt[:200],
            "completion": completion,
            "tokens": len(tokens),
            "gt_span": gt_span,
            "severe": severe,
            "api_token_repeat": api_vote,
            "api_confidence": api_conf,
            "engine_token_repeat": eng_vote,
            "engine_span": eng_span,
            "engine_votes": eng_votes,
        })

        flag = "SEVERE" if severe else "      "
        print(
            f"[{i:>3}] tokens={len(tokens):>4} gt_span={gt_span:>3} {flag} "
            f"api={int(bool(api_vote))} engine={int(bool(eng_vote))} conf={api_conf:.2f}"
        )

    if not rows:
        sys.exit("no completions generated")

    severe = [r for r in rows if r["severe"]]
    clean = [r for r in rows if not r["severe"]]

    tp = sum(1 for r in severe if r["api_token_repeat"])
    fn = len(severe) - tp
    fp = sum(1 for r in clean if r["api_token_repeat"])
    tn = len(clean) - fp

    spans = [r["gt_span"] for r in rows]

    sweep = {}
    for threshold in SWEEP_SPANS:
        s_tp = s_fp = s_fn = s_tn = 0
        for r in rows:
            vote = bool(r.get("engine_votes", {}).get(str(threshold)))
            if r["severe"] and vote:
                s_tp += 1
            elif r["severe"]:
                s_fn += 1
            elif vote:
                s_fp += 1
            else:
                s_tn += 1
        sweep[str(threshold)] = {
            "tp": s_tp, "fp": s_fp, "fn": s_fn, "tn": s_tn,
            "precision": ratio(s_tp, s_tp + s_fp),
            "recall": ratio(s_tp, s_tp + s_fn),
            "f1": ratio(2 * s_tp, 2 * s_tp + s_fp + s_fn),
            "false_positive_rate": ratio(s_fp, s_fp + s_tn),
        }

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "samples": len(rows),
        "severe_threshold": SEVERE_SPAN,
        "detector_threshold": DETECTOR_SPAN,
        "severe": len(severe),
        "clean": len(clean),
        "api": {
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": ratio(tp, tp + fp),
            "recall": ratio(tp, tp + fn),
            "f1": ratio(2 * tp, 2 * tp + fp + fn),
            "false_positive_rate": ratio(fp, fp + tn),
        },
        "engine_token_repeat_matches_api": sum(
            1 for r in rows if bool(r["engine_token_repeat"]) == bool(r["api_token_repeat"])
        ),
        "threshold_sweep": sweep,
        "gt_span": {
            "min": min(spans),
            "median": statistics.median(spans),
            "max": max(spans),
            "in_6_to_15": sum(1 for s in spans if DETECTOR_SPAN <= s < SEVERE_SPAN),
        },
        "rows": rows,
    }

    reports_dir = Path(__file__).resolve().parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    out = reports_dir / f"antidoom_benchmark_{int(time.time())}.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"samples           : {summary['samples']}")
    print(f"severe (gt>={SEVERE_SPAN})  : {summary['severe']}")
    print(f"api precision     : {summary['api']['precision']}")
    print(f"api recall        : {summary['api']['recall']}")
    print(f"api f1            : {summary['api']['f1']}")
    print(f"api false-pos rate: {summary['api']['false_positive_rate']}")
    print(f"engine == api     : {summary['engine_token_repeat_matches_api']}/{summary['samples']}")
    print(f"gt span median    : {summary['gt_span']['median']} (max {summary['gt_span']['max']})")
    print("\nthreshold sweep (engine detector)")
    print(f"  {'span':>4}  {'precision':>9}  {'recall':>6}  {'f1':>6}  {'fpr':>6}")
    for threshold in SWEEP_SPANS:
        s = summary["threshold_sweep"][str(threshold)]
        print(
            f"  {threshold:>4}  {str(s['precision']):>9}  {str(s['recall']):>6}  "
            f"{str(s['f1']):>6}  {str(s['false_positive_rate']):>6}"
        )
    print(f"report            : {out}")


if __name__ == "__main__":
    main()
