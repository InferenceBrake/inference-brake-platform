import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const supabase = createClient(
	Deno.env.get("SUPABASE_URL")!,
	Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

const model = new Supabase.ai.Session("gte-small");

// --- Client-side detectors: edit distance, NCD ---

function wordLevenshtein(a: string[], b: string[]): number {
	if (a.length < b.length) return wordLevenshtein(b, a);
	if (b.length === 0) return a.length;
	let prev = Array.from({ length: b.length + 1 }, (_, i) => i);
	for (let i = 0; i < a.length; i++) {
		const curr = [i + 1];
		for (let j = 0; j < b.length; j++) {
			curr.push(Math.min(
				prev[j + 1] + 1,
				curr[j] + 1,
				prev[j] + (a[i] !== b[j] ? 1 : 0),
			));
		}
		prev = curr;
	}
	return prev[b.length];
}

function normalizedEditDistance(textA: string, textB: string): number {
	const wordsA = textA.toLowerCase().replace(/\s+/g, " ").trim().split(" ").filter(Boolean);
	const wordsB = textB.toLowerCase().replace(/\s+/g, " ").trim().split(" ").filter(Boolean);
	if (wordsA.length === 0 && wordsB.length === 0) return 0;
	const maxWords = Math.max(wordsA.length, wordsB.length);
	if (maxWords === 0) return 0;
	return Math.min(wordLevenshtein(wordsA, wordsB) / maxWords, 1.0);
}

async function compressedSize(text: string): Promise<number> {
	const input = new TextEncoder().encode(text);
	const cs = new CompressionStream("gzip");
	const writer = cs.writable.getWriter();
	writer.write(input);
	writer.close();
	let size = 0;
	const reader = cs.readable.getReader();
	while (true) {
		const { done, value } = await reader.read();
		if (done) break;
		size += value.byteLength;
	}
	return size;
}

async function ncdSimilarity(textA: string, textB: string): Promise<number> {
	if (!textA || !textB || textA.length < 20 || textB.length < 20) return 0;
	const [cA, cB, cAB] = await Promise.all([
		compressedSize(textA),
		compressedSize(textB),
		compressedSize(textA + textB),
	]);
	const denom = Math.max(cA, cB);
	if (denom === 0) return 0;
	const ncd = (cAB - Math.min(cA, cB)) / denom;
	return 1.0 - Math.max(0, Math.min(ncd, 1.0));
}

// --- Main handler ---

Deno.serve(async (req) => {
	if (req.method === "OPTIONS")
		return new Response("ok", { headers: corsHeaders });

	try {
		// 1. AUTH
		const authHeader = req.headers.get("Authorization");
		const apiKey = authHeader?.replace("Bearer ", "");
		if (!apiKey) throw new Error("Missing API Key");

		const { data: user, error: authError } = await supabase
			.from("users")
			.select("*")
			.or(`api_key.eq.${apiKey},test_mode_api_key.eq.${apiKey}`)
			.single();

		if (authError || !user)
			return new Response(JSON.stringify({ error: "Invalid API Key" }), {
				status: 401,
				headers: { ...corsHeaders, "Content-Type": "application/json" },
			});

		const isTestMode = user.test_mode === true || user.test_mode_api_key === apiKey;

		// 2. RATE LIMIT (check before increment to avoid phantom counts)
		let currentChecks = user.checks_today || 0;
		// Beta mode: generous free tier - 10k checks/day
		const dailyLimit = user.daily_limit || 10000;

		if (!isTestMode) {
			if (user.subscription_status === "past_due") {
				return new Response(JSON.stringify({ error: "Subscription past due. Update payment." }), {
					status: 402,
					headers: { ...corsHeaders, "Content-Type": "application/json" },
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
					},
				});
			}

			// Increment after check passes (fixes phantom count bug)
			await supabase.rpc("increment_usage", { user_uuid: user.id });
			currentChecks += 1;
		}

		const remaining = dailyLimit - currentChecks;

		// 3. PARSE
		const body = await req.json();
		const { session_id, reasoning, action: reqAction } = body;

		// 4. EMBEDDING + HISTORY (parallel)
		const [embeddingResult, historyResult] = await Promise.all([
			model.run(reasoning, { mean_pool: true, normalize: true }),
			supabase
				.from("reasoning_history")
				.select("step_number, reasoning")
				.eq("session_id", session_id)
				.order("step_number", { ascending: false })
				.limit(5),
		]);

		const embedding = embeddingResult;
		const recentSteps = historyResult.data || [];
		const nextStep = (recentSteps[0]?.step_number || 0) + 1;
		const recentTexts: string[] = recentSteps
			.map((s: { reasoning: string }) => s.reasoning)
			.filter(Boolean)
			.reverse();

		// 5. SQL DETECTORS (semantic, action, ngram)
		const { data: loopResult } = await supabase.rpc("detect_semantic_loop", {
			target_session_id: session_id,
			new_embedding: embedding,
			match_threshold: 0.85,
			action_repeat_limit: 3,
			ngram_threshold: 0.5,
		});

		const similarity = loopResult?.[0]?.max_similarity || 0;
		const actionRepeatCount = loopResult?.[0]?.action_repeat_count || 0;
		const ngramOverlap = loopResult?.[0]?.ngram_overlap || 0;
		const semanticVote = loopResult?.[0]?.semantic_vote || false;
		const actionVote = loopResult?.[0]?.action_vote || false;
		const ngramVote = loopResult?.[0]?.ngram_vote || false;

		// 6. CLIENT-SIDE DETECTORS (edit distance, NCD)
		let editDistVote = false;
		let editDistScore = 1.0;
		let ncdVote = false;
		let ncdScore = 0;

		if (recentTexts.length >= 2) {
			// Edit distance: consecutive deltas, stasis check
			const deltas: number[] = [];
			for (let i = 1; i < recentTexts.length; i++) {
				deltas.push(normalizedEditDistance(recentTexts[i - 1], recentTexts[i]));
			}
			const currentDelta = normalizedEditDistance(
				recentTexts[recentTexts.length - 1],
				reasoning,
			);
			deltas.push(currentDelta);
			editDistScore = currentDelta;

			// Stasis: last 2+ of 3 deltas below 0.08
			const recent3 = deltas.slice(-3);
			const stasisCount = recent3.filter(d => d < 0.08).length;
			editDistVote = stasisCount >= 2;

			// NCD: max similarity against recent steps
			const ncdSims = await Promise.all(
				recentTexts.map(prev => ncdSimilarity(prev, reasoning)),
			);
			ncdScore = Math.max(...ncdSims, 0);
			ncdVote = ncdScore >= 0.80;
		}

		// 7. WEIGHTED VOTING (5 detectors)
		// semantic=1.5, action=1.0, ngram=1.0, editdist=1.0, compression=1.0
		const totalWeight = 5.5;
		let weightedSum = 0;
		if (semanticVote) weightedSum += 1.5;
		if (actionVote) weightedSum += 1.0;
		if (ngramVote) weightedSum += 1.0;
		if (editDistVote) weightedSum += 1.0;
		if (ncdVote) weightedSum += 1.0;
		const confidence = weightedSum / totalWeight;
		const isLooping = confidence >= 0.5;  // Default threshold

		const extractedAction: string = reqAction
			?? reasoning.split(" ")[0]?.toLowerCase().slice(0, 50)
			?? "unknown";

		// 8. ASYNC LOGGING
		Promise.all([
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
						editdist_vote: editDistVote,
						editdist_score: editDistScore,
						ncd_vote: ncdVote,
						ncd_score: ncdScore,
						confidence,
					},
				})
				.then(({ error }) => {
					if (error) console.error("History log failed:", error.message);
				}),

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
					if (error) console.error("Metrics log failed:", error.message);
				}),
		]).catch((err) => console.error("Background logging error:", err));

		// 9. RESPONSE
		const action = isLooping ? "KILL" : "PROCEED";

		const now = new Date();
		const tomorrow = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + 1));
		const resetTimestamp = Math.floor(tomorrow.getTime() / 1000);

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
					editdist: editDistVote,
					compression: ncdVote,
				},
				confidence: Math.round(confidence * 100) / 100,
				status: isLooping ? "danger" : "safe",
				message: isLooping
					? `Loop detected (confidence=${(confidence * 100).toFixed(0)}%)`
					: "Reasoning sound",
				test_mode: isTestMode,
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
					"X-RateLimit-Remaining": String(isTestMode ? dailyLimit : Math.max(0, remaining)),
					"X-RateLimit-Reset": String(resetTimestamp),
				},
			},
		);
	} catch (err) {
		return new Response(JSON.stringify({ error: err.message }), {
			status: 500,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}
});

const corsHeaders = {
	"Access-Control-Allow-Origin": "*",
	"Access-Control-Allow-Headers":
		"authorization, x-client-info, apikey, content-type",
};
