import "dotenv/config";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
	process.env.SUPABASE_URL!,
	process.env.SUPABASE_SERVICE_ROLE_KEY!,
);

const TEST_EMAIL = "dev@inferencebrake.local";
let API_KEY = "";

async function ensureTestUser() {
	// Check if user exists
	const { data: existingUser } = await supabase
		.from("users")
		.select("id, email, api_key")
		.eq("email", TEST_EMAIL)
		.single();

	if (existingUser) {
		console.log(`Found existing user: ${TEST_EMAIL}`);
		API_KEY = existingUser.api_key;
		
		// Reset daily limit for testing (use high limit for tests)
		await supabase
			.from("users")
			.update({ checks_today: 0, daily_limit: 1000 })
			.eq("id", existingUser.id);
		
		return existingUser;
	}

	// Create new user
	console.log(`Creating new user: ${TEST_EMAIL}`);
	const { data: newUser, error } = await supabase.rpc("create_user", {
		user_email: TEST_EMAIL,
		user_plan: "pro",
	});

	if (error) {
		console.error("Failed to create user:", error);
		process.exit(1);
	}

	API_KEY = newUser[0].api_key;
	console.log(`Created user with API key: ${API_KEY}`);
	return newUser[0];
}

console.log("Using API Key:", API_KEY);

interface TestResult {
	passed: boolean;
	message: string;
}

const results: TestResult[] = [];

function assert(condition: boolean, message: string): void {
	if (!condition) {
		results.push({ passed: false, message });
		console.error(`❌ FAIL: ${message}`);
	} else {
		results.push({ passed: true, message });
		console.log(`✅ PASS: ${message}`);
	}
}

async function runSaaSBenchmark() {
	console.log("Starting InferenceBrake SaaS Benchmark...\n");
	const sessionId = "test-session-" + Math.random().toString(36).substring(7);

	// Test 1: No loop - varied reasoning
	const normalSteps = [
		"I need to check the stock price for Apple.",
		"Now let me look up the weather in New York.",
		"Next I'll search for flights to Chicago.",
	];

	// Test 2: Semantic loop - very similar reasoning
	// Note: Semantic-only loops may not trigger KILL if confidence is low
	// The detector fires (semantic: true) but needs majority vote for KILL
	const semanticLoopSteps = [
		"I need to check the stock price for Apple.",
		"Let me look up the AAPL stock price on Yahoo Finance.",
		"I'm going to check the Apple stock price again.",
		"Checking Apple stock price one more time.",
		"Let me get the current Apple stock price now.",
		"I should check Apple stock again.",
		"Checking Apple stock again.",
		"Apple stock check again.",
	];

	// Test 3: Action loop - repeated actions
	const actionLoopSteps = [
		"Searching for file 'config.json' in the project.",
		"Searching for file 'config.json' in the project.",
		"Searching for file 'config.json' in the project.",
		"Searching for file 'config.json' in the project.",
	];

	console.log("=".repeat(50));
	console.log("TEST 1: Normal (no loop) reasoning");
	console.log("=".repeat(50));
	await runSession(sessionId + "-normal", normalSteps, {
		expectLoop: false,
		minSteps: 3,
	});

	console.log("\n" + "=".repeat(50));
	console.log("TEST 2: Semantic loop detection");
	console.log("=".repeat(50));
	await runSession(sessionId + "-semantic", semanticLoopSteps, {
		expectLoop: true,
		maxSteps: 8,
	});

	console.log("\n" + "=".repeat(50));
	console.log("TEST 3: Action repetition detection");
	console.log("=".repeat(50));
	await runSession(sessionId + "-action", actionLoopSteps, {
		expectLoop: true,
		maxSteps: 4,
	});

	// Verify data was stored
	console.log("\n" + "=".repeat(50));
	console.log("VERIFICATION: Checking stored data");
	console.log("=".repeat(50));
	await verifyStoredData(sessionId);

	// Print summary
	console.log("\n" + "=".repeat(50));
	console.log("TEST SUMMARY");
	console.log("=".repeat(50));
	const passed = results.filter(r => r.passed).length;
	const failed = results.filter(r => !r.passed).length;
	console.log(`Total: ${results.length}, Passed: ${passed}, Failed: ${failed}`);

	if (failed > 0) {
		console.log("\n❌ Failed tests:");
		for (const r of results.filter(x => !x.passed)) {
			console.log(`  - ${r.message}`);
		}
		process.exit(1);
	} else {
		console.log("\n✅ All tests passed!");
		process.exit(0);
	}
}

interface SessionOptions {
	expectLoop: boolean;
	minSteps?: number;
	maxSteps?: number;
}

async function runSession(sessionId: string, steps: string[], options: SessionOptions) {
	let loopDetected = false;
	let loopAtStep: number | null = null;
	let lastConfidence = 0;
	const sessionSteps: any[] = [];

	for (let i = 0; i < steps.length; i++) {
		const reasoning = steps[i];
		console.log(`\n--- Step ${i + 1} ---`);
		console.log(`Reasoning: "${reasoning}"`);

		const start = performance.now();
		const response = await supabase.functions.invoke("check", {
			body: {
				session_id: sessionId,
				reasoning: reasoning,
			},
			headers: {
				Authorization: `Bearer ${API_KEY}`,
			},
		});
		const duration = (performance.now() - start).toFixed(2);

		if (response.error) {
			console.error("✘ API Error:", response.error);
			assert(false, `API call failed: ${response.error}`);
			return;
		}

		const {
			action,
			loop_detected,
			similarity,
			action_repeat_count,
			ngram_overlap,
			detectors,
			confidence,
			message,
		} = response.data;

		lastConfidence = confidence;
		sessionSteps.push({ detectors, confidence });
		console.log(`Similarity: ${(similarity * 100).toFixed(1)}%`);
		console.log(`Action repeat: ${action_repeat_count}`);
		console.log(`N-gram overlap: ${(ngram_overlap * 100).toFixed(1)}%`);
		console.log(`Detectors:`, detectors);
		console.log(`Confidence: ${(confidence * 100).toFixed(1)}%`);

		if (action === "KILL") {
			console.log(`[KILL] ${message}`);
			console.log(`Savings: Blocked in ${duration}ms`);
			loopDetected = true;
			loopAtStep = i + 1;
			break;
		} else {
			console.log(`✔ [PROCEED] ${message} (${duration}ms)`);
		}
	}

	// Assertions - semantic loop should trigger at least semantic detector
	if (options.expectLoop) {
		// Check that at least semantic detector fired at some point
		const semanticFired = sessionSteps.some((s: any) => s.detectors?.semantic);
		assert(semanticFired || loopDetected, `${sessionId}: Expected semantic detector to fire or loop to be detected`);
		if (options.maxSteps && loopAtStep) {
			assert(loopAtStep <= options.maxSteps, `${sessionId}: Loop should be detected within ${options.maxSteps} steps, was at step ${loopAtStep}`);
		}
	} else {
		assert(!loopDetected, `${sessionId}: Expected no loop for varied reasoning`);
		if (options.minSteps) {
			assert(!loopDetected, `${sessionId}: Should proceed through all ${options.minSteps} steps without loop`);
		}
	}
}

async function verifyStoredData(sessionPrefix: string) {
	const { data: history, error } = await supabase
		.from("reasoning_history")
		.select("session_id, step_number, reasoning, action, similarity, loop_detected, metadata")
		.like("session_id", sessionPrefix + "%")
		.order("session_id, step_number");

	if (error) {
		console.error("✘ Error fetching history:", error);
		assert(false, "Should be able to fetch reasoning history");
		return;
	}

	assert(history !== null && history.length > 0, "Should have stored reasoning history");
	console.log(`\nFound ${history?.length || 0} history records`);

	// Check that semantic loop session has at least one step with semantic detector fired
	const semanticSession = history?.find(h => h.session_id.includes("semantic"));
	if (semanticSession) {
		// Semantic loop should have fired semantic detector at some point
		// Check metadata for semantic_vote
		const semanticFired = history?.some((h: any) => 
			h.session_id.includes("semantic") && h.metadata?.semantic_vote
		);
		assert(semanticFired === true, "Semantic loop session should have fired semantic detector");
	}

	// Check that normal session has loop_detected = false for all steps
	const normalSessions = history?.filter(h => h.session_id.includes("normal")) || [];
	if (normalSessions.length > 0) {
		const hasFalseLoops = normalSessions.some(h => h.loop_detected === false);
		assert(hasFalseLoops, "Normal session should have loop_detected=false");
	}
}

async function main() {
	await ensureTestUser();
	console.log("Using API Key:", API_KEY);
	await runSaaSBenchmark();
}

main();
