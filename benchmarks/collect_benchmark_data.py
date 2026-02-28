#!/usr/bin/env python3
"""
InferenceBrake Benchmark Data Collection Script

Downloads and processes real agent traces from HuggingFace datasets:
- PatronusAI/TRAIL
- McGill-NLP/agent-reward-bench
- AmineHA/WebArena-Verified
- princeton-nlp/SWE-bench-verified

Usage:
    python collect_benchmark_data.py

Output:
    benchmark_data/
    ├── trail_traces.json
    ├── agent_reward_bench_traces.json
    ├── webarena_verified_traces.json
    ├── swebench_verified_traces.json
    ├── synthetic_traces.json
    └── all_traces.json
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datasets import load_dataset
import random


class BenchmarkDataCollector:
    """
    Collect agent traces from multiple HuggingFace datasets
    """

    def __init__(self, output_dir="benchmark_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        print(f"[DIR] Output directory: {self.output_dir.absolute()}")

    def save(self, data: List[Dict], filename: str):
        """Save data to JSON"""
        filepath = self.output_dir / filename
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        print(f"   [SAVED] Saved to {filename}")

    def collect_trail(self) -> List[Dict]:
        """
        TRAIL dataset - Debug agent errors, hallucination detection
        Extracts actual agent reasoning from nested span structure
        """
        print("\n[COLLECT] Collecting TRAIL data...")

        try:
            dataset = load_dataset("PatronusAI/TRAIL")
            traces = []
            error_count = 0

            for split in dataset.keys():
                for idx, item in enumerate(dataset[split]):
                    try:
                        item_dict = dict(item)
                        
                        # Parse trace string (handle malformed JSON)
                        trace_str = item_dict.get("trace", "{}")
                        try:
                            trace_data = json.loads(trace_str)
                        except json.JSONDecodeError:
                            # Try to fix common JSON issues
                            trace_str = trace_str.replace(',]', ']').replace(',}', '}')
                            try:
                                trace_data = json.loads(trace_str)
                            except:
                                error_count += 1
                                continue
                                
                        spans = trace_data.get("spans", [])
                        
                        # Parse labels for success/failure
                        labels = item_dict.get("labels", {})
                        if isinstance(labels, str):
                            try:
                                labels = json.loads(labels)
                            except:
                                labels = {}
                            
                        errors = labels.get("errors", [])
                        has_errors = len(errors) > 0
                        
                         # Extract steps from spans recursively
                        def extract_steps_from_span(span, step_list, depth=0):
                            """Recursively extract steps from span and its children"""
                            # Get span info
                            span_name = span.get('span_name', 'unknown')
                            
                            # Try to get actual reasoning from logs or attributes
                            reasoning = span_name
                            logs = span.get('logs', [])
                            if logs:
                                # Concatenate log messages
                                log_msgs = []
                                for log in logs[:5]:  # Limit to first 5 logs
                                    if isinstance(log, dict):
                                        msg = log.get('body', '')
                                        # Handle dict bodies (common in TRAIL)
                                        if isinstance(msg, dict):
                                            msg = json.dumps(msg)[:200]
                                        elif msg:
                                            msg = str(msg)
                                    else:
                                        msg = str(log)
                                    if msg:
                                        log_msgs.append(msg)
                                if log_msgs:
                                    reasoning = ' | '.join(log_msgs)
                            
                            # Get attributes that might contain actual content
                            attrs = span.get('attributes', {})
                            if isinstance(attrs, dict):
                                # Look for reasoning/thought content
                                for key in ['reasoning', 'thought', 'input', 'query', 'prompt', 'content']:
                                    if key in attrs:
                                        reasoning = str(attrs[key])
                                        break
                            
                            step_list.append({
                                "reasoning": reasoning,
                                "action": span.get("span_kind", "unknown"),
                                "observation": str(attrs) if attrs else "",
                                "metadata": {
                                    "span_id": span.get("span_id"),
                                    "span_name": span_name,
                                    "depth": depth,
                                    "timestamp": span.get("timestamp")
                                }
                            })
                            
                            # Process child spans recursively
                            child_spans = span.get('child_spans', [])
                            for child in child_spans:
                                extract_steps_from_span(child, step_list, depth + 1)
                        
                         # Extract all steps from all top-level spans
                        steps = []
                        for span in spans:
                            extract_steps_from_span(span, steps)
                        
                        # Only keep traces with actual content (multiple steps)
                        if len(steps) < 2:
                            continue
                        
                        # Extract error evidence as additional context
                        error_evidence = []
                        for err in errors[:3]:  # First 3 errors
                            evidence = err.get('evidence', '')
                            if evidence:
                                error_evidence.append(evidence[:200])

                        traces.append(
                            {
                                "id": f"trail_{split}_{trace_data.get('trace_id', len(traces))}",
                                "source": "trail",
                                "steps": steps,
                                "query": "See trace spans",
                                "has_hallucination": has_errors,
                                "success": not has_errors,
                                "label": "no_loop",  # TRAIL errors = hallucination, NOT looping. This was a labeling bug.
                                "loop_type": None,  # Requires human annotation to determine if error = loop
                                "error_evidence": error_evidence,
                                "metadata": {
                                    "split": split,
                                    "error_count": len(errors),
                                    "score": labels.get("scores", [{}])[0].get("overall", 0) if labels.get("scores") else 0,
                                    "step_count": len(steps),
                                    "note": "has_errors indicates hallucination, not looping. Label set to no_loop for conservative benchmark.",
                                },
                            }
                        )
                    except Exception as e:
                        # Skip malformed items
                        continue

            print(f"   [OK] Collected {len(traces)} TRAIL traces with {sum(len(t['steps']) for t in traces)} total steps")
            self.save(traces, "trail_traces.json")
            return traces

        except Exception as e:
            print(f"   [ERR] TRAIL error: {e}")
            import traceback
            traceback.print_exc()
            return []

    def collect_agent_reward_bench(self) -> List[Dict]:
        """
        McGill-NLP/agent-reward-bench - Agent evaluation labels
        NOTE: This dataset contains evaluation metadata only, NOT actual agent trajectories.
        It's not useful for loop detection benchmarking.
        """
        print("\n[COLLECT] Checking Agent Reward Bench data...")
        print("   [INFO] This dataset contains evaluation labels only, not execution traces.")
        print("   [INFO] Skipping - not useful for loop detection.")
        return []

    def collect_webarena_verified(self) -> List[Dict]:
        """
        AmineHA/WebArena-Verified - Web agent task definitions
        NOTE: This dataset contains task specifications, NOT actual agent execution traces.
        It's not useful for loop detection benchmarking.
        """
        print("\n[COLLECT] Checking WebArena-Verified data...")
        print("   [INFO] This dataset contains task definitions only, not execution traces.")
        print("   [INFO] Skipping - not useful for loop detection.")
        return []

    def collect_swebench_verified(self) -> List[Dict]:
        """
        princeton-nlp/SWE-bench_Verified - Software engineering problems and patches
        NOTE: This dataset contains problem statements and solutions, not actual agent traces.
        We create synthetic multi-step "coding workflows" for variety.
        """
        print("\n[COLLECT] Collecting SWE-bench-Verified data...")

        try:
            # Use correct dataset ID with underscore
            dataset = load_dataset(
                "princeton-nlp/SWE-bench_Verified", split="test"
            )
            traces = []

            for idx, item in enumerate(dataset):
                item_dict = dict(item)
                problem = str(item_dict.get("problem_statement", ""))
                patch = str(item_dict.get("patch", ""))
                instance_id = str(item_dict.get("instance_id", ""))
                
                # Create a realistic multi-step coding workflow
                # Simulate an agent trying to fix the bug
                steps = [
                    {
                        "reasoning": f"Understanding the issue: {problem[:100]}...",
                        "action": "read_issue",
                        "observation": f"Instance: {instance_id}",
                    },
                    {
                        "reasoning": "Exploring the codebase to find relevant files...",
                        "action": "search_files",
                        "observation": "Found potential files",
                    },
                    {
                        "reasoning": "Reading the code to understand the bug...",
                        "action": "read_code",
                        "observation": "Located problematic function",
                    },
                    {
                        "reasoning": f"Implementing the fix: {patch[:150] if patch else 'applying patch'}...",
                        "action": "edit_code",
                        "observation": "Patch applied successfully",
                    },
                ]

                traces.append(
                    {
                        "id": f"swebench_verified_{instance_id}",
                        "source": "swebench_verified",
                        "steps": steps,
                        "success": True,  # These are resolved issues
                        "problem_statement": problem[:500],
                        "metadata": {
                            "repo": str(item_dict.get("repo", "")),
                            "step_count": len(steps),
                        },
                    }
                )
                
                # Limit to first 100 for speed
                if idx >= 99:
                    break

            print(f"   [OK] Collected {len(traces)} SWE-bench-Verified traces")
            self.save(traces, "swebench_verified_traces.json")
            return traces

        except Exception as e:
            print(f"   [ERR] SWE-bench-Verified error: {e}")
            import traceback
            traceback.print_exc()
            return []

    def generate_synthetic_loops(self, n=500) -> List[Dict]:
        """
        Generate comprehensive synthetic loop cases for testing
        Creates realistic, long-horizon agent traces with various loop patterns
        """
        print(f"\n[GEN] Generating {n} comprehensive synthetic traces...")

        traces = []
        templates = 8  # Number of different loop types + healthy
        traces_per_template = n // templates

        # Template 1: Semantic loops - Agent stuck on same concept with varied wording (10 steps)
        semantic_variations = [
            "I need to check the current weather conditions in New York City",
            "Let me look up NYC weather information right now",
            "I should find out what the weather is like in New York",
            "Looking up weather data for New York City today",
            "Checking NYC weather forecast and current conditions",
            "I want to see the weather report for New York",
            "Searching for current NYC weather information",
            "Let me find the weather details for New York City",
            "Trying to get the latest weather update for NYC",
            "Still searching for New York weather information",
        ]
        for i in range(traces_per_template):
            steps = [{"reasoning": v, "action": f"search_{j}", "observation": None} 
                     for j, v in enumerate(semantic_variations)]
            traces.append({
                "id": f"synthetic_semantic_{i}",
                "source": "synthetic",
                "steps": steps,
                "label": "loop",
                "loop_type": "semantic",
                "success": False,
                "metadata": {"template": "semantic_loop", "step_count": len(steps)},
            })

        # Template 2: Action loops - Same action repeated (8 steps)
        action_reasonings = [
            "Clicking the submit button to send the form",
            "Form didn't submit, trying to click submit again",
            "Still no response, attempting to click submit once more",
            "Submit button not working, trying click again",
            "Let me try clicking submit one more time",
            "Form submission failed, clicking submit again",
            "Trying submit button again to see if it works",
            "Clicking submit once more hoping for success",
        ]
        for i in range(traces_per_template):
            steps = [{"reasoning": r, "action": "click_submit", "observation": "No response"}
                     for r in action_reasonings]
            traces.append({
                "id": f"synthetic_action_{i}",
                "source": "synthetic",
                "steps": steps,
                "label": "loop",
                "loop_type": "action",
                "success": False,
                "metadata": {"template": "action_loop", "step_count": len(steps)},
            })

        # Template 3: CUSUM loops - Semantic drift decaying toward stagnation (10 steps)
        # Start normal, gradually become repetitive
        cusum_steps = [
            "Analyzing the data structure to understand the schema",
            "Examining the data more carefully for interesting patterns",
            "Looking at the data to find relevant patterns in the dataset",
            "Checking the data for any patterns that might help",
            "Reviewing the data once more to identify useful patterns",
            "Looking again at the data structure to find patterns",
            "Analyzing the data once more for any patterns",
            "Reviewing data structure patterns again",
            "Checking data for patterns again",
            "Looking at data patterns once more",
        ]
        for i in range(traces_per_template):
            steps = [{"reasoning": r, "action": "analyze", "observation": "No progress"}
                     for r in cusum_steps]
            traces.append({
                "id": f"synthetic_cusum_{i}",
                "source": "synthetic",
                "steps": steps,
                "label": "loop",
                "loop_type": "cusum",
                "success": False,
                "metadata": {"template": "cusum_loop", "step_count": len(steps)},
            })

        # Template 4: N-gram loops - High textual overlap with variations (10 steps)
        ngram_steps = [
            "Processing the user request and checking the database status",
            "Processing the request and verifying the current status",
            "Processing user request and checking the system status",
            "Processing the request and checking database status again",
            "Processing user request, verifying the current status",
            "Processing the request and checking the status once more",
            "Processing request again and checking the current status",
            "Processing the user request and verifying status again",
            "Processing request and checking database status",
            "Processing the request again to check current status",
        ]
        for i in range(traces_per_template):
            steps = [{"reasoning": r, "action": "process", "observation": None}
                     for r in ngram_steps]
            traces.append({
                "id": f"synthetic_ngram_{i}",
                "source": "synthetic",
                "steps": steps,
                "label": "loop",
                "loop_type": "ngram",
                "success": False,
                "metadata": {"template": "ngram_loop", "step_count": len(steps)},
            })

        # Template 5: Entropy loops - Gradual vocabulary collapse (8 steps)
        entropy_steps = [
            "I am analyzing the system status and checking the current state",
            "Checking the system and analyzing current state information",
            "Analyzing system state and checking current status",
            "Checking system status and state analysis",
            "System status checking and analysis",
            "Checking status and system analysis",
            "Status checking system analysis",
            "checking checking checking",
        ]
        for i in range(traces_per_template):
            steps = [{"reasoning": r, "action": "check", "observation": None}
                     for r in entropy_steps]
            traces.append({
                "id": f"synthetic_entropy_{i}",
                "source": "synthetic",
                "steps": steps,
                "label": "loop",
                "loop_type": "entropy",
                "success": False,
                "metadata": {"template": "entropy_loop", "step_count": len(steps)},
            })

        # Template 6: Mixed pattern loops - Semantic + Action combined (12 steps)
        # Agent tries different approaches but keeps hitting same issue
        mixed_steps = [
            {"reasoning": "User wants to search for product information", "action": "search_product", "observation": "Searching..."},
            {"reasoning": "Search returned no results, trying different keywords", "action": "search_alt", "observation": "No matches"},
            {"reasoning": "Still no results, let me try the original search again", "action": "search_product", "observation": "Searching..."},
            {"reasoning": "Trying another search with modified terms", "action": "search_modified", "observation": "No results"},
            {"reasoning": "Let me go back to the first search approach", "action": "search_product", "observation": "Searching..."},
            {"reasoning": "Trying a completely different search strategy", "action": "search_new", "observation": "Nothing found"},
            {"reasoning": "Going to try the original search one more time", "action": "search_product", "observation": "Searching..."},
            {"reasoning": "Maybe I should search with the first method again", "action": "search_product", "observation": "Searching..."},
        ]
        for i in range(traces_per_template):
            traces.append({
                "id": f"synthetic_mixed_{i}",
                "source": "synthetic",
                "steps": mixed_steps,
                "label": "loop",
                "loop_type": "semantic",  # Mixed but primarily semantic
                "success": False,
                "metadata": {"template": "mixed_loop", "step_count": len(mixed_steps)},
            })

        # Template 7: Navigation loops - Web browsing stuck in cycles (10 steps)
        nav_steps = [
            {"reasoning": "Navigating to homepage to start search", "action": "navigate_home", "observation": "Page loaded"},
            {"reasoning": "Clicking on products section", "action": "click_products", "observation": "Products page"},
            {"reasoning": "Going back to homepage to try different approach", "action": "navigate_home", "observation": "Page loaded"},
            {"reasoning": "Trying products category again", "action": "click_products", "observation": "Products page"},
            {"reasoning": "Let me return to homepage and check menu", "action": "navigate_home", "observation": "Page loaded"},
            {"reasoning": "Clicking on products link once more", "action": "click_products", "observation": "Products page"},
            {"reasoning": "Going back to homepage to reconsider strategy", "action": "navigate_home", "observation": "Page loaded"},
            {"reasoning": "Trying products section again", "action": "click_products", "observation": "Products page"},
        ]
        for i in range(traces_per_template):
            traces.append({
                "id": f"synthetic_nav_{i}",
                "source": "synthetic",
                "steps": nav_steps,
                "label": "loop",
                "loop_type": "action",  # Navigation loop detected by action repetition
                "success": False,
                "metadata": {"template": "navigation_loop", "step_count": len(nav_steps)},
            })

        # Template 8: No loops - Healthy multi-step execution (12 steps)
        healthy_steps = [
            {"reasoning": "User wants to book a flight from NYC to LA for next week", "action": "init_search", "observation": "Ready"},
            {"reasoning": "Searching for available flights on the requested dates", "action": "search_flights", "observation": "Found 15 flights"},
            {"reasoning": "Filtering flights by direct routes and reasonable prices", "action": "filter_flights", "observation": "5 options remaining"},
            {"reasoning": "Comparing flight times and prices for the 5 options", "action": "compare_options", "observation": "Comparison complete"},
            {"reasoning": "Selected the best option: 8am departure, $350, direct", "action": "select_flight", "observation": "Flight selected"},
            {"reasoning": "Collecting passenger information for booking", "action": "collect_pax_info", "observation": "Info received"},
            {"reasoning": "Validating passenger details and passport information", "action": "validate_pax", "observation": "Validation passed"},
            {"reasoning": "Processing payment with user's credit card", "action": "process_payment", "observation": "Payment successful"},
            {"reasoning": "Generating booking confirmation and e-tickets", "action": "generate_tickets", "observation": "Tickets ready"},
            {"reasoning": "Sending confirmation email with booking details", "action": "send_email", "observation": "Email sent"},
            {"reasoning": "Booking complete! Providing summary to user", "action": "finalize", "observation": "Success"},
        ]
        for i in range(traces_per_template):
            traces.append({
                "id": f"synthetic_healthy_{i}",
                "source": "synthetic",
                "steps": healthy_steps,
                "label": "no_loop",
                "loop_type": None,
                "success": True,
                "metadata": {"template": "healthy_execution", "step_count": len(healthy_steps)},
            })

        print(f"   [OK] Generated {len(traces)} synthetic traces")
        self.save(traces, "synthetic_traces.json")
        return traces

    def collect_all(self) -> List[Dict]:
        """Collect all available datasets"""

        print("=" * 60)
        print("InferenceBrake Benchmark Data Collection")
        print("=" * 60)

        all_traces = []

        # 1. Synthetic data (High quality ground truth) - PUT FIRST
        # Increased count to 500 to ensure good coverage in limited runs
        all_traces.extend(self.generate_synthetic_loops(500))

        # 2. Real datasets (keep only usable ones)
        # TRAIL has actual execution traces with error annotations (most valuable)
        trail_traces = self.collect_trail()
        all_traces.extend(trail_traces)
        
        # WebArena and AgentRewardBench don't have execution traces (skip)
        # all_traces.extend(self.collect_webarena_verified())
        # all_traces.extend(self.collect_agent_reward_bench())
        
        # SWE-bench has problem statements, we create synthetic coding workflows
        all_traces.extend(self.collect_swebench_verified())

        # Save combined
        self.save(all_traces, "all_traces.json")

        print("\n" + "=" * 60)
        print("[COMPLETE] DATA COLLECTION COMPLETE")
        print("=" * 60)
        print(f"Total traces: {len(all_traces)}")
        print(f"\nBreakdown by source:")
        print(
            f"   - Synthetic:            {sum(1 for t in all_traces if t.get('source') == 'synthetic')}"
        )
        print(
            f"   - TRAIL:                {sum(1 for t in all_traces if t.get('source') == 'trail')}"
        )
        print(
            f"   - WebArena:             {sum(1 for t in all_traces if t.get('source') == 'webarena_verified')}"
        )
        print(
            f"   - AgentRewardBench:     {sum(1 for t in all_traces if t.get('source') == 'agent_reward_bench')}"
        )
        print(
            f"   - SWE-bench:            {sum(1 for t in all_traces if t.get('source') == 'swebench_verified')}"
        )
        print("=" * 60)

        return all_traces


def main():
    """Main entry point"""
    collector = BenchmarkDataCollector()
    traces = collector.collect_all()

    print(f"\n[READY] Ready to benchmark on {len(traces)} traces!")
    print(f"[DIR] Data saved to: {collector.output_dir.absolute()}")
    print(f"\nNext steps:")
    print(f"   1. Review the data in benchmark_data/all_traces.json")
    print(f"   2. Run your InferenceBrake pipeline on these traces")
    print(f"   3. Calculate accuracy, precision, recall metrics")


if __name__ == "__main__":
    main()
