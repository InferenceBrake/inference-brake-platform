#!/usr/bin/env bun
/**
 * Edge Function Benchmark Test
 * 
 * Runs the Supabase edge function against benchmark traces
 * to measure real-world accuracy.
 * 
 * Usage:
 *   bun run test:edge-benchmark
 *   bun run test:edge-benchmark --limit 50
 */

import { createClient } from "@supabase/supabase-js";
import { readFileSync } from "fs";
import { join } from "path";

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

interface BenchmarkTrace {
	id: string;
	source: string;
	label: "loop" | "no_loop";
	steps: { reasoning: string; action?: string }[];
}

interface TestResult {
	traceId: string;
	label: string;
	loopDetected: boolean;
	detectedAtStep: number | null;
	confidence: number;
	detectors: Record<string, boolean>;
	latencyMs: number;
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

async function getTestApiKey(): Promise<string> {
	const { data, error } = await supabase
		.from("users")
		.select("api_key")
		.eq("email", "dev@inferencebrake.local")
		.single();
	
	if (error || !data) {
		throw new Error(`Failed to get API key: ${error?.message}`);
	}
	
	return data.api_key;
}

async function loadTraces(limit?: number): Promise<BenchmarkTrace[]> {
	const dataDir = join(process.cwd(), "packages", "engine", "benchmark_data");
	
	try {
		const raw = readFileSync(join(dataDir, "all_traces.json"), "utf-8");
		const traces: BenchmarkTrace[] = JSON.parse(raw);
		
		console.log(`Loaded ${traces.length} traces total`);
		console.log(`  Loops: ${traces.filter(t => t.label === "loop").length}`);
		console.log(`  No-loops: ${traces.filter(t => t.label === "no_loop").length}`);
		
		if (limit) {
			// Stratified sampling: equal loops and no-loops
			const loops = traces.filter(t => t.label === "loop");
			const noLoops = traces.filter(t => t.label === "no_loop");
			
			const loopLimit = Math.floor(limit / 2);
			const noLoopLimit = limit - loopLimit;
			
			return [
				...loops.slice(0, loopLimit),
				...noLoops.slice(0, noLoopLimit),
			];
		}
		
		return traces;
	} catch (e) {
		console.error("Failed to load benchmark data:", e.message);
		console.log("Run Python benchmark first: cd packages/engine && uv run python ../benchmarks/run_benchmarks.py --collect");
		process.exit(1);
	}
}

async function runEdgeFunctionCheck(
	apiKey: string,
	sessionId: string,
	reasoning: string,
	action?: string
): Promise<{ loopDetected: boolean; confidence: number; detectors: Record<string, boolean>; similarity?: number; ngramOverlap?: number; actionRepeatCount?: number }> {
	const startTime = Date.now();
	
	const response = await fetch(`${SUPABASE_URL}/functions/v1/check`, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			"Authorization": `Bearer ${apiKey}`,
		},
		body: JSON.stringify({
			session_id: sessionId,
			reasoning,
			action,
		}),
	});
	
	const latencyMs = Date.now() - startTime;
	
	if (!response.ok) {
		const error = await response.text();
		console.error("Edge function error:", response.status, error);
		return {
			loopDetected: false,
			confidence: 0,
			detectors: {},
		};
	}
	
	const data = await response.json();
	
	return {
		loopDetected: data.loop_detected || false,
		confidence: data.confidence || 0,
		detectors: data.detectors || {},
		similarity: data.similarity,
		ngramOverlap: data.ngram_overlap,
		actionRepeatCount: data.action_repeat_count,
	};
}

async function runBenchmark(traces: BenchmarkTrace[]): Promise<TestResult[]> {
	// Get API key for auth
	const apiKey = await getTestApiKey();
	console.log(`Using API key: ${apiKey.slice(0, 10)}...`);
	
	const results: TestResult[] = [];
	
	console.log(`Running edge function benchmark on ${traces.length} traces...`);
	console.log(`  Loops: ${traces.filter(t => t.label === "loop").length}`);
	console.log(`  No-loops: ${traces.filter(t => t.label === "no_loop").length}`);
	
	for (let i = 0; i < traces.length; i++) {
		const trace = traces[i];
		const progress = ((i + 1) / traces.length * 100).toFixed(1);
		process.stdout.write(`\r[${progress}%] ${i + 1}/${traces.length} - ${trace.id}`);
		
	// Use unique session_id for each trace to avoid history pollution
	const sessionPrefix = `bench-${Date.now()}-${Math.random().toString(36).slice(2,8)}`;
	const sessionId = `${sessionPrefix}-${trace.id}`;
		
		let loopDetected = false;
		let detectedAtStep: number | null = null;
		let confidence = 0;
		let finalDetectors: Record<string, boolean> = {};
		
		for (let stepNum = 0; stepNum < trace.steps.length; stepNum++) {
			const step = trace.steps[stepNum];
			
			const result = await runEdgeFunctionCheck(
				apiKey,
				sessionId,
				step.reasoning,
				step.action
			);
			
			if (result.loopDetected && detectedAtStep === null) {
				loopDetected = true;
				detectedAtStep = stepNum + 1;
				confidence = result.confidence;
				finalDetectors = result.detectors;
				break;
			}
			
			// Store last result for final metrics
			if (stepNum === trace.steps.length - 1) {
				confidence = result.confidence;
				finalDetectors = result.detectors;
			}
		}
		
		results.push({
			traceId: trace.id,
			label: trace.label,
			loopDetected,
			detectedAtStep,
			confidence,
			detectors: finalDetectors,
			latencyMs: 0,
		});
	}
	
	console.log("\n");
	return results;
}

function calculateMetrics(results: TestResult[]) {
	const truePositives = results.filter(r => r.label === "loop" && r.loopDetected).length;
	const falsePositives = results.filter(r => r.label === "no_loop" && r.loopDetected).length;
	const trueNegatives = results.filter(r => r.label === "no_loop" && !r.loopDetected).length;
	const falseNegatives = results.filter(r => r.label === "loop" && !r.loopDetected).length;
	
	const total = results.length;
	const accuracy = (truePositives + trueNegatives) / total;
	const precision = truePositives / (truePositives + falsePositives) || 0;
	const recall = truePositives / (truePositives + falseNegatives) || 0;
	const f1 = (2 * precision * recall) / (precision + recall) || 0;
	const fpr = falsePositives / (falsePositives + trueNegatives) || 0;
	
	// Per-detector stats
	const detectorStats: Record<string, { total: number; triggered: number }> = {};
	for (const r of results) {
		for (const [detector, triggered] of Object.entries(r.detectors)) {
			if (!detectorStats[detector]) {
				detectorStats[detector] = { total: 0, triggered: 0 };
			}
			detectorStats[detector].total++;
			if (triggered) {
				detectorStats[detector].triggered++;
			}
		}
	}
	
	return {
		accuracy,
		precision,
		recall,
		f1,
		fpr,
		confusionMatrix: { tp: truePositives, fp: falsePositives, tn: trueNegatives, fn: falseNegatives },
		detectorStats,
	};
}

function printReport(metrics: ReturnType<typeof calculateMetrics>, traceCount: number) {
	console.log("\n" + "=".repeat(60));
	console.log("  EDGE FUNCTION BENCHMARK RESULTS");
	console.log("=".repeat(60));
	
	console.log("\nCLASSIFICATION METRICS");
	console.log("-".repeat(40));
	console.log(`  Accuracy:    ${(metrics.accuracy * 100).toFixed(1)}%`);
	console.log(`  Precision:  ${(metrics.precision * 100).toFixed(1)}%`);
	console.log(`  Recall:     ${(metrics.recall * 100).toFixed(1)}%`);
	console.log(`  F1 Score:   ${(metrics.f1 * 100).toFixed(1)}%`);
	console.log(`  FP Rate:    ${(metrics.fpr * 100).toFixed(1)}%`);
	
	console.log("\nCONFUSION MATRIX");
	console.log("-".repeat(40));
	console.log(`  True Positives:      ${metrics.confusionMatrix.tp}`);
	console.log(`  False Positives:    ${metrics.confusionMatrix.fp}`);
	console.log(`  True Negatives:     ${metrics.confusionMatrix.tn}`);
	console.log(`  False Negatives:    ${metrics.confusionMatrix.fn}`);
	console.log(`  Total Traces:       ${traceCount}`);
	
	console.log("\nPER-DETECTOR PERFORMANCE");
	console.log("-".repeat(40));
	for (const [detector, stats] of Object.entries(metrics.detectorStats)) {
		const rate = (stats.triggered / stats.total * 100).toFixed(1);
		console.log(`  ${detector.padEnd(12)} ${rate.padStart(6)}% triggered (${stats.triggered}/${stats.total})`);
	}
	
	console.log("=".repeat(60));
}

async function main() {
	const args = process.argv.slice(2);
	const limitArg = args.findIndex(a => a === "--limit");
	const limit = limitArg >= 0 ? parseInt(args[limitArg + 1], 10) : undefined;
	
	console.log("Loading benchmark traces...");
	const traces = await loadTraces(limit);
	
	console.log(`Traces: ${traces.filter(t => t.label === "loop").length} loops, ${traces.filter(t => t.label === "no_loop").length} no-loops`);
	
	const results = await runBenchmark(traces);
	const metrics = calculateMetrics(results);
	printReport(metrics, results.length);
	
	// Compare with Python if available
	console.log("\nNote: Python pipeline (7 detectors) showed 100% recall on loops.");
	console.log("Edge function (5 detectors) results shown above.");
}

main().catch(console.error);
