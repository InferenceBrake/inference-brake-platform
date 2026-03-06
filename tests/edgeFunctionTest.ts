import "dotenv/config";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
	process.env.SUPABASE_URL!,
	process.env.SUPABASE_SERVICE_ROLE_KEY!,
);

const TEST_EMAIL = "dev@inferencebrake.local";
let API_KEY = "";

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

async function ensureTestUser() {
	const { data: existingUser } = await supabase
		.from("users")
		.select("id, email, api_key")
		.eq("email", TEST_EMAIL)
		.single();

	if (existingUser) {
		console.log(`Found existing user: ${TEST_EMAIL}`);
		API_KEY = existingUser.api_key;
		return existingUser;
	}

	console.error("User dev@inferencebrake.local not found!");
	process.exit(1);
}

async function runHealthCheckTest() {
	console.log("\n=== TEST: Health Check Endpoint ===\n");

	const response = await fetch(`${process.env.SUPABASE_URL}/functions/v1/health`, {
		method: "GET",
	});

	assert(response.ok || response.status === 503, "Health endpoint should respond");

	const data = await response.json();
	console.log("Health response:", JSON.stringify(data, null, 2));

	assert(data.status !== undefined, "Health response should have status field");
	assert(data.services?.database !== undefined, "Health response should have database status");

	console.log(`Status: ${data.status}`);
	console.log(`Database: ${data.services?.database?.status}`);
}

async function runGenerateTestKeyTest() {
	console.log("\n=== TEST: Generate Test Key ===\n");

	const response = await supabase.functions.invoke("generate-test-key", {
		headers: {
			Authorization: `Bearer ${API_KEY}`,
		},
	});

	if (response.error) {
		assert(false, `Generate test key failed: ${response.error}`);
		return;
	}

	assert(response.data?.success === true, "Should return success");
	assert(response.data?.test_api_key?.startsWith("ib_test_"), "Should return test API key starting with ib_test_");

	console.log("Generated test key:", response.data.test_api_key);

	const { data: user } = await supabase
		.from("users")
		.select("test_mode, test_mode_api_key")
		.eq("api_key", API_KEY)
		.single();

	assert(user?.test_mode === true, "User should have test_mode enabled");
	assert(user?.test_mode_api_key === response.data.test_api_key, "Test key should be stored in database");
}

async function runTestModeApiTest() {
	console.log("\n=== TEST: Test Mode API Key Works ===\n");

	const { data: user } = await supabase
		.from("users")
		.select("test_mode_api_key")
		.eq("api_key", API_KEY)
		.single();

	if (!user?.test_mode_api_key) {
		console.log("Skipping - no test key generated yet");
		return;
	}

	const sessionId = "test-mode-session-" + Math.random().toString(36).substring(7);
	const reasoning = "Testing in test mode - this should not count against limit";

	const response = await supabase.functions.invoke("check", {
		body: {
			session_id: sessionId,
			reasoning: reasoning,
		},
		headers: {
			Authorization: `Bearer ${user.test_mode_api_key}`,
		},
	});

	if (response.error) {
		assert(false, `Test mode API call failed: ${response.error}`);
		return;
	}

	assert(response.data?.test_mode === true, "Response should indicate test_mode");
	console.log("Test mode response:", response.data.test_mode);
}

async function runDataExportTest() {
	console.log("\n=== TEST: Data Export ===\n");

	const response = await supabase.functions.invoke("data-export", {
		headers: {
			Authorization: `Bearer ${API_KEY}`,
		},
	});

	if (response.error) {
		assert(false, `Data export failed: ${response.error}`);
		return;
	}

	assert(response.data?.exported_at !== undefined, "Should have exported_at timestamp");
	assert(response.data?.user !== undefined, "Should have user data");
	assert(response.data?.reasoning_history !== undefined, "Should have reasoning_history");
	assert(Array.isArray(response.data?.reasoning_history), "Reasoning history should be an array");

	console.log("Data export successful");
	console.log("Records:", response.data.total_records);
}

async function runHealthCheckProductionTest() {
	console.log("\n=== TEST: Health Check Production ===\n");

	const prodUrl = process.env.SUPABASE_URL;
	if (!prodUrl) {
		console.log("Production URL not set - skipping production test");
		return;
	}
	
	try {
		const response = await fetch(`${prodUrl}/functions/v1/health`, {
			method: "GET",
		});

		if (response.ok) {
			const data = await response.json();
			console.log("Production health:", data);
			assert(data.status === "healthy", "Production should be healthy");
		} else {
			console.log("Production not accessible or not healthy");
		}
	} catch (e) {
		console.log("Production health check skipped (not accessible)");
	}
}

async function main() {
	await ensureTestUser();
	console.log("Using API Key:", API_KEY);

	await runHealthCheckTest();
	await runGenerateTestKeyTest();
	await runTestModeApiTest();
	await runDataExportTest();
	await runHealthCheckProductionTest();

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

main();
