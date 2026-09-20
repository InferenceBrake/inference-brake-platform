import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";
import { PLANS, FREE_PLAN } from "../_shared/plans.ts";
import { buildAlertHtml, buildAlertText, buildSlackMessage, emailConfigured, sendEmail, sendSlack } from "../_shared/alerts.ts";

const supabase = createClient(
	Deno.env.get("SUPABASE_URL")!,
	Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

const model = new Supabase.ai.Session("gte-small");

// --- Cost model ---
// A detected loop is assumed to have continued for LOOP_STEPS_AVOIDED more
// reasoning steps had it not been halted. Each step's output token count is
// estimated with words * TOKENS_PER_WORD (same convention as the Python
// engine, pipeline.py). Priced at OUTPUT_PRICE_PER_TOKEN (USD), defaulting to
// $10 / 1M tokens (GPT-4o-class output). Override via env vars.
const TOKENS_PER_WORD = 1.3;
const LOOP_STEPS_AVOIDED = Number(Deno.env.get("LOOP_STEPS_AVOIDED") ?? 10);
const OUTPUT_PRICE_PER_TOKEN = Number(
	Deno.env.get("OUTPUT_PRICE_PER_TOKEN") ?? 0.00001,
);

function estimateTokens(text: string): number {
	const words = text.trim().split(/\s+/).filter(Boolean).length;
	return Math.ceil(words * TOKENS_PER_WORD);
}

function estimateCostSaved(tokens: number, isLooping: boolean): number {
	if (!isLooping) return 0;
	return tokens * LOOP_STEPS_AVOIDED * OUTPUT_PRICE_PER_TOKEN;
}

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

// --- Token repetition (exact repeated spans) ---
// Mirrors the failure mode Antidoom targets at training time and OpenRouter
// detects for exact repeats, but available at runtime for any framework.

const TOKEN_REPEAT_MIN_SPAN = 10;
const TOKEN_REPEAT_MAX_TOKENS = 800;

function tokenizeWords(text: string): string[] {
	return text.toLowerCase().match(/[a-z0-9']+/g) ?? [];
}

function longestRepeatedSpan(tokens: string[]): number {
	const n = tokens.length;
	if (n < 2) return 0;
	let best = 0;
	let prev = new Array<number>(n + 1).fill(0);
	for (let i = 1; i <= n; i++) {
		const curr = new Array<number>(n + 1).fill(0);
		for (let j = 1; j < i; j++) {
			if (tokens[i - 1] === tokens[j - 1]) {
				const len = prev[j - 1] + 1;
				curr[j] = len;
				if (len > best) best = len;
			}
		}
		prev = curr;
	}
	return best;
}

function longestCommonSpan(a: string[], b: string[]): number {
	if (!a.length || !b.length) return 0;
	if (b.length > a.length) {
		const swap = a;
		a = b;
		b = swap;
	}
	let best = 0;
	let prev = new Array<number>(b.length + 1).fill(0);
	for (let i = 1; i <= a.length; i++) {
		const curr = new Array<number>(b.length + 1).fill(0);
		for (let j = 1; j <= b.length; j++) {
			if (a[i - 1] === b[j - 1]) {
				const len = prev[j - 1] + 1;
				curr[j] = len;
				if (len > best) best = len;
			}
		}
		prev = curr;
	}
	return best;
}

function tokenRepeatSpan(reasoning: string, recentTexts: string[]): number {
	const tokens = tokenizeWords(reasoning).slice(0, TOKEN_REPEAT_MAX_TOKENS);
	if (tokens.length < 3) return 0;
	let best = longestRepeatedSpan(tokens);
	for (const prev of recentTexts) {
		const prevTokens = tokenizeWords(prev).slice(0, TOKEN_REPEAT_MAX_TOKENS);
		const common = longestCommonSpan(tokens, prevTokens);
		if (common > best) best = common;
	}
	return best;
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
		const checksToday = user.checks_today || 0;
		let currentChecks = user.checks_this_month || 0;
		const monthlyLimit = user.monthly_limit || PLANS[FREE_PLAN].monthlyLimit;

		if (!isTestMode) {
			if (user.subscription_status === "past_due") {
				return new Response(JSON.stringify({ error: "Subscription past due. Update payment." }), {
					status: 402,
					headers: { ...corsHeaders, "Content-Type": "application/json" },
				});
			}

			if (currentChecks >= monthlyLimit) {
				return new Response(JSON.stringify({
					error: "Monthly quota exceeded",
					limit: monthlyLimit,
					used: currentChecks,
				}), {
					status: 429,
					headers: {
						...corsHeaders,
						"Content-Type": "application/json",
						"X-RateLimit-Limit": String(monthlyLimit),
						"X-RateLimit-Remaining": "0",
					},
				});
			}

			// Increment after check passes (fixes phantom count bug)
			await supabase.rpc("increment_usage", { user_uuid: user.id });
			currentChecks += 1;
		}

		const remaining = monthlyLimit - currentChecks;

		// 3. PARSE
		const body = await req.json();
		const { session_id, reasoning, action: reqAction, model: reqModel, prompt: reqPrompt } = body;

		// 4. EMBEDDING + HISTORY (parallel)
		const [embeddingResult, historyResult] = await Promise.all([
			model.run(reasoning, { mean_pool: true, normalize: true }),
			supabase
				.from("reasoning_history")
				.select("step_number, reasoning, loop_detected")
				.eq("session_id", session_id)
				.order("step_number", { ascending: false })
				.limit(5),
		]);

		const embedding = embeddingResult;
		const recentSteps = historyResult.data || [];
		const nextStep = (recentSteps[0]?.step_number || 0) + 1;
		const previousWasLoop = recentSteps[0]?.loop_detected === true;
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

		// Token repetition: exact repeated spans (intra-text and vs recent steps)
		const tokenRepeatScore = tokenRepeatSpan(reasoning, recentTexts);
		const tokenRepeatVote = tokenRepeatScore >= TOKEN_REPEAT_MIN_SPAN;

		// 7. WEIGHTED VOTING (6 detectors)
		// semantic=1.5, token_repeat=1.2, action=1.0, ngram=1.0, editdist=1.0, compression=1.0
		const totalWeight = 6.7;
		let weightedSum = 0;
		if (semanticVote) weightedSum += 1.5;
		if (actionVote) weightedSum += 1.0;
		if (ngramVote) weightedSum += 1.0;
		if (editDistVote) weightedSum += 1.0;
		if (ncdVote) weightedSum += 1.0;
		if (tokenRepeatVote) weightedSum += 1.2;
		const confidence = weightedSum / totalWeight;
		const isLooping = confidence >= 0.5;  // Default threshold

		const extractedAction: string = reqAction
			?? reasoning.split(" ")[0]?.toLowerCase().slice(0, 50)
			?? "unknown";

		// 7b. COST ESTIMATE
		const tokenCount = estimateTokens(reasoning);
		const costSaved = estimateCostSaved(tokenCount, isLooping);

		// 7c. ALERTS (best-effort, first loop of a session only)
		if (isLooping && !previousWasLoop && user.alerts_enabled !== false) {
			const alertPayload = {
				session_id,
				reasoning,
				confidence,
				detectors: {
					semantic: semanticVote,
					action: actionVote,
					ngram: ngramVote,
					editdist: editDistVote,
					compression: ncdVote,
					token_repeat: tokenRepeatVote,
				},
				action: extractedAction,
				model: reqModel ?? null,
				estimated_cost_saved: costSaved,
			};
			const alertText = buildAlertText(alertPayload);
			const alertHtml = buildAlertHtml(alertPayload);
			const slack = buildSlackMessage(alertPayload);

			const emailConfig = emailConfigured();
			if (user.alert_email && emailConfig) {
				sendEmail({
					apiKey: emailConfig.apiKey,
					from: emailConfig.from,
					to: user.alert_email,
					subject: "InferenceBrake: loop detected and halted",
					text: alertText,
					html: alertHtml,
				}).then((r) => {
					if (!r.ok) console.error("Email alert failed:", r.error);
				});
			}

			if (user.webhook_url) {
				sendSlack(user.webhook_url, slack.text, slack.blocks).then((r) => {
					if (!r.ok) console.error("Webhook alert failed:", r.error);
				});
			}
		}

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
						token_repeat_vote: tokenRepeatVote,
						token_repeat_score: tokenRepeatScore,
						confidence,
						token_count: tokenCount,
						estimated_cost_saved: costSaved,
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
					estimated_cost_saved: costSaved,
					model: reqModel ? String(reqModel).slice(0, 100) : null,
					action: extractedAction,
					prompt: reqPrompt ? String(reqPrompt).slice(0, 200) : null,
					confidence,
					detectors: {
						semantic: semanticVote,
						action: actionVote,
						ngram: ngramVote,
						editdist: editDistVote,
						compression: ncdVote,
						token_repeat: tokenRepeatVote,
					},
				})
				.then(({ error }) => {
					if (error) console.error("Metrics log failed:", error.message);
				}),
		]).catch((err) => console.error("Background logging error:", err));

		// 9. RESPONSE
		const action = isLooping ? "KILL" : "PROCEED";

		const now = new Date();
		const nextMonth = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + 1, 1));
		const resetTimestamp = Math.floor(nextMonth.getTime() / 1000);

		return new Response(
			JSON.stringify({
				action,
				loop_detected: isLooping,
				similarity,
				estimated_cost_saved: costSaved,
				action_repeat_count: actionRepeatCount,
				ngram_overlap: ngramOverlap,
				detectors: {
					semantic: semanticVote,
					action: actionVote,
					ngram: ngramVote,
					editdist: editDistVote,
					compression: ncdVote,
					token_repeat: tokenRepeatVote,
				},
				confidence: Math.round(confidence * 100) / 100,
				status: isLooping ? "danger" : "safe",
				message: isLooping
					? `Loop detected (confidence=${(confidence * 100).toFixed(0)}%)`
					: "Reasoning sound",
				test_mode: isTestMode,
				usage: {
					today: checksToday,
					month: currentChecks,
					limit: monthlyLimit,
					remaining: Math.max(0, remaining),
				},
			}),
			{
				headers: {
					...corsHeaders,
					"Content-Type": "application/json",
					"X-RateLimit-Limit": String(monthlyLimit),
					"X-RateLimit-Remaining": String(isTestMode ? monthlyLimit : Math.max(0, remaining)),
					"X-RateLimit-Period": "month",
					"X-RateLimit-Reset": String(resetTimestamp),
				},
			},
		);
	} catch (err) {
		return new Response(JSON.stringify({ error: err instanceof Error ? err.message : String(err) }), {
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
