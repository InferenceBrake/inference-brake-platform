import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

// Initialize Supabase with Service Role (required for RLS bypass & AI)
const supabase = createClient(
	Deno.env.get("SUPABASE_URL")!,
	Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

// Free Built-in Model
const model = new Supabase.ai.Session("gte-small");

Deno.serve(async (req) => {
	// 1. CORS & Methods (From their file)
	if (req.method === "OPTIONS")
		return new Response("ok", { headers: corsHeaders });

	try {
		// 2. AUTHENTICATION (The "SaaS" part)
		const authHeader = req.headers.get("Authorization");
		const apiKey = authHeader?.replace("Bearer ", "");

		if (!apiKey) throw new Error("Missing API Key");

		const { data: user, error: authError } = await supabase
			.from("users")
			.select("*")
			.eq("api_key", apiKey)
			.single();

		if (authError || !user)
			return new Response(JSON.stringify({ error: "Invalid API Key" }), {
				status: 401,
			});

		// 3. INCREMENT USAGE FIRST (synchronously, so rate limit check is accurate)
		await supabase
			.rpc("increment_usage", {
				user_uuid: user.id,
			});

		// Re-fetch user to get updated checks_today
		const { data: updatedUser } = await supabase
			.from("users")
			.select("checks_today, daily_limit, subscription_status")
			.eq("id", user.id)
			.single();

		const currentChecks = updatedUser?.checks_today || user.checks_today + 1;
		const dailyLimit = updatedUser?.daily_limit || user.daily_limit;

		// Calculate reset time (midnight UTC)
		const now = new Date();
		const tomorrow = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + 1));
		const resetTimestamp = Math.floor(tomorrow.getTime() / 1000);

		// 4. RATE LIMIT CHECK (after increment)
		if (updatedUser?.subscription_status === 'past_due') {
			return new Response(JSON.stringify({ error: "Subscription past due. Please update payment." }), {
				status: 402,
			});
		}
		
		if (currentChecks >= dailyLimit) {
			return new Response(JSON.stringify({ 
				error: "Rate limit exceeded",
				limit: dailyLimit,
				used: currentChecks,
			}), {
				status: 429,
				headers: {
					...corsHeaders,
					"Content-Type": "application/json",
					"X-RateLimit-Limit": String(dailyLimit),
					"X-RateLimit-Remaining": "0",
					"X-RateLimit-Reset": String(resetTimestamp),
				},
			});
		}
		
		const remaining = dailyLimit - currentChecks;

		// 5. PARSE REQUEST (read body once - streams are single-use)
		const body = await req.json();
		const { session_id, reasoning, action: reqAction } = body;

		// 5. GENERATE EMBEDDING (The "Free" part - No OpenAI!)
		const embedding = await model.run(reasoning, {
			mean_pool: true,
			normalize: true,
		});

		// 6. DETECT LOOP (The "Fast" part - SQL RPC with multi-detector)
		const { data: loopResult } = await supabase.rpc("detect_semantic_loop", {
			target_session_id: session_id,
			new_embedding: embedding,
			match_threshold: 0.85,
			action_repeat_limit: 3,
			ngram_threshold: 0.5,
		});

		const isLooping = loopResult?.[0]?.loop_detected || false;
		const similarity = loopResult?.[0]?.max_similarity || 0;
		const actionRepeatCount = loopResult?.[0]?.action_repeat_count || 0;
		const ngramOverlap = loopResult?.[0]?.ngram_overlap || 0;
		const semanticVote = loopResult?.[0]?.semantic_vote || false;
		const actionVote = loopResult?.[0]?.action_vote || false;
		const ngramVote = loopResult?.[0]?.ngram_vote || false;
		const confidence = loopResult?.[0]?.overall_confidence || 0;

		// Extract action from request body, or fall back to first word of reasoning
		const extractedAction: string = reqAction
			?? reasoning.split(" ")[0]?.toLowerCase().slice(0, 50)
			?? "unknown";

		const { data: previousSteps } = await supabase
			.from("reasoning_history")
			.select("step_number")
			.eq("session_id", session_id)
			.order("step_number", { ascending: false })
			.limit(1);

		const nextStep = (previousSteps?.[0]?.step_number || 0) + 1;

		// 7. ASYNC LOGGING (The background "SaaS" work)
		// We don't 'await' this Promise.all so the user gets their response immediately
		// Note: increment_usage already called synchronously above
		Promise.all([
			// Task A: Save this step to history for future loop detection
			supabase
				.from("reasoning_history")
				.insert({
					session_id,
					user_id: user.id,
					step_number: nextStep,
					reasoning,
					action: extractedAction,
					embedding,
					similarity,
					loop_detected: isLooping,
					metadata: {
						action_repeat_count: actionRepeatCount,
						ngram_overlap: ngramOverlap,
						semantic_vote: semanticVote,
						action_vote: actionVote,
						ngram_vote: ngramVote,
						confidence: confidence,
					},
				})
				.then(({ error }) => {
					if (error) console.error("✘ History Log Failed:", error.message);
				}),

			// Task C: Log to metrics for analytics
				supabase
				.from("metrics")
				.insert({
					user_id: user.id,
					session_id,
					loop_detected: isLooping,
					similarity,
					estimated_cost_saved: null,
				})
				.then(({ error }) => {
					if (error) console.error("✘ Metrics Log Failed:", error.message);
				}),
		]).catch((err) => console.error("🚨 Background Logging Error:", err));

		// 8. RETURN RESPONSE
		const action = isLooping ? "KILL" : "PROCEED";
		return new Response(
			JSON.stringify({
				action,
				loop_detected: isLooping,
				similarity,
				action_repeat_count: actionRepeatCount,
				ngram_overlap: ngramOverlap,
				detectors: {
					semantic: semanticVote,
					action: actionVote,
					ngram: ngramVote,
				},
				confidence: Math.round(confidence * 100) / 100,
				status: isLooping ? "danger" : "safe",
				message: isLooping 
					? `Loop detected: semantic=${semanticVote}, action=${actionVote}, ngram=${ngramVote}`
					: "Reasoning sound",
				usage: {
					today: currentChecks,
					limit: dailyLimit,
					remaining: Math.max(0, remaining),
				},
			}),
			{ 
				headers: { 
					...corsHeaders, 
					"Content-Type": "application/json",
					"X-RateLimit-Limit": String(dailyLimit),
					"X-RateLimit-Remaining": String(Math.max(0, remaining)),
					"X-RateLimit-Reset": String(resetTimestamp),
				} 
			},
		);
	} catch (err) {
		return new Response(JSON.stringify({ error: err.message }), {
			status: 500,
		});
	}
});

const corsHeaders = {
	"Access-Control-Allow-Origin": "*",
	"Access-Control-Allow-Headers":
		"authorization, x-client-info, apikey, content-type",
};
