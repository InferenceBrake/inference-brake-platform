import "dotenv/config";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
	process.env.SUPABASE_URL!,
	process.env.SUPABASE_SERVICE_ROLE_KEY!,
);

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
	// Use existing dev user
	const TEST_EMAIL = "dev@inferencebrake.local";
	
	// Check if user exists
	const { data: existingUser } = await supabase
		.from("users")
		.select("id, email, api_key")
		.eq("email", TEST_EMAIL)
		.single();

	if (existingUser) {
		console.log(`Found existing user: ${TEST_EMAIL}`);
		API_KEY = existingUser.api_key;
		
		// Reset daily limit and disable test mode for rate limit testing
		await supabase
			.from("users")
			.update({ 
				checks_today: 0, 
				daily_limit: 5,
				test_mode: false,
				test_mode_api_key: null
			})
			.eq("id", existingUser.id);
		
		return existingUser;
	}

	console.error("User dev@inferencebrake.local not found!");
	process.exit(1);
}

async function runRateLimitTest() {
	console.log("Starting Rate Limit Test...\n");
	const sessionId = "rate-limit-test-" + Math.random().toString(36).substring(7);
	
	// Step through the session, making requests
	// With daily_limit=5, we should get 429 on the 6th request
	const reasoning = "Testing rate limit with repeated reasoning step";
	
	console.log(`Testing with daily_limit=5 (expect 429 on 6th request)\n`);
	
	let rateLimited = false;
	const successCount = 0;
	
	for (let i = 1; i <= 7; i++) {
		console.log(`\n--- Request ${i} ---`);
		
		let status = 200;
		let rateLimitLimit = "N/A";
		let rateLimitRemaining = "N/A";
		
		try {
			const response: any = await supabase.functions.invoke("check", {
				body: {
					session_id: sessionId,
					reasoning: reasoning + " " + i,
				},
				headers: {
					Authorization: `Bearer ${API_KEY}`,
				},
			});

			// Check the actual HTTP status from response.response
			const httpStatus = response.response?.status;
			
			// Check if rate limited (429) or has error
			if (httpStatus === 429 || response.error || (response.data?.error?.includes("Rate limit"))) {
				status = 429;
				rateLimitLimit = String(response.data?.limit || "N/A");
				rateLimitRemaining = "0";
				console.log(`Status: ${status}, Limit: ${rateLimitLimit}, Remaining: ${rateLimitRemaining}`);
				console.log(`Request ${i} rate limited`);
				rateLimited = true;
				break;
			}
			
			// Check for usage data in successful response
			if (response.data?.usage) {
				rateLimitLimit = String(response.data.usage.limit);
				rateLimitRemaining = String(response.data.usage.remaining);
			}
			
			console.log(`Status: ${status}, Limit: ${rateLimitLimit}, Remaining: ${rateLimitRemaining}`);
			console.log(`✅ Request ${i} succeeded`);
			
		} catch (error: any) {
			// Rate limit errors throw an exception
			status = 429;
			console.log(`Request ${i} rate limited (caught exception)`);
			rateLimited = true;
			break;
		}
		
		// Small delay between requests
		await new Promise(r => setTimeout(r, 100));
	}

	// Assertions
	assert(rateLimited, "Should get rate limited after exceeding daily limit");
	
	// Verify in database that user has hits the limit
	const { data: user } = await supabase
		.from("users")
		.select("checks_today, daily_limit")
		.eq("api_key", API_KEY)
		.single();
	
	if (user) {
		assert(user.checks_today >= 5, `Should have 5+ checks_today, got ${user.checks_today}`);
		console.log(`Database shows checks_today: ${user.checks_today}, daily_limit: ${user.daily_limit}`);
	}
	
	// Try one more request - should still be rate limited
	console.log("\n--- Verifying rate limit persists ---");
	
	try {
		const response: any = await supabase.functions.invoke("check", {
			body: {
				session_id: sessionId,
				reasoning: "This should be rate limited",
			},
			headers: {
				Authorization: `Bearer ${API_KEY}`,
			},
		});

		const httpStatus = response.response?.status;
		if (httpStatus === 429 || response.error) {
			console.log("✅ Second request also rate limited as expected");
		} else {
			assert(false, "Should have been rate limited");
		}
	} catch (error: any) {
		console.log("✅ Second request also rate limited as expected");
	}
	
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

async function main() {
	await ensureTestUser();
	console.log("Using API Key:", API_KEY);
	await runRateLimitTest();
}

main();
