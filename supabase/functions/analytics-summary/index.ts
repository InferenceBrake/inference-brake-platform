import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const corsHeaders = {
	"Access-Control-Allow-Origin": "*",
	"Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

// Returns usage and dollars-saved analytics for the authenticated user.
Deno.serve(async (req) => {
	if (req.method === "OPTIONS") {
		return new Response("ok", { headers: corsHeaders });
	}

	try {
		const apiKey = req.headers.get("Authorization")?.replace("Bearer ", "");
		if (!apiKey) {
			return json({ error: "Missing API key" }, 401);
		}

		const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
		const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
		const authHeaders = {
			apikey: supabaseKey,
			Authorization: `Bearer ${supabaseKey}`,
		};

		const userRes = await fetch(
			`${supabaseUrl}/rest/v1/users?api_key=eq.${apiKey}&select=id,plan,monthly_limit`,
			{ headers: authHeaders },
		);
		const users = await userRes.json();
		const user = users[0];

		if (!user) {
			return json({ error: "Invalid API key" }, 401);
		}

		let days = 30;
		if (req.method === "POST") {
			const body = await req.json().catch(() => ({}));
			if (typeof body?.days === "number" && body.days > 0 && body.days <= 365) {
				days = Math.floor(body.days);
			}
		} else {
			const param = new URL(req.url).searchParams.get("days");
			if (param && Number(param) > 0 && Number(param) <= 365) {
				days = Math.floor(Number(param));
			}
		}

		const rpcRes = await fetch(`${supabaseUrl}/rest/v1/rpc/analytics_summary`, {
			method: "POST",
			headers: { ...authHeaders, "Content-Type": "application/json" },
			body: JSON.stringify({ p_user_id: user.id, p_days: days }),
		});

		if (!rpcRes.ok) {
			const detail = await rpcRes.text();
			return json({ error: "Analytics query failed", detail }, 500);
		}

		const summary = await rpcRes.json();

		return json({
			plan: user.plan,
			days,
			total_checks: summary.total_checks ?? 0,
			loops_blocked: summary.loops_blocked ?? 0,
			estimated_usd_saved: summary.estimated_usd_saved ?? 0,
			window_days: summary.window_days ?? days,
			window_checks: summary.window_checks ?? 0,
			window_loops: summary.window_loops ?? 0,
			window_usd_saved: summary.window_usd_saved ?? 0,
			avg_similarity: summary.avg_similarity ?? 0,
			first_check_at: summary.first_check_at ?? null,
			last_check_at: summary.last_check_at ?? null,
			daily: summary.daily ?? [],
			by_model: summary.by_model ?? [],
			by_action: summary.by_action ?? [],
			by_prompt: summary.by_prompt ?? [],
			by_detector: summary.by_detector ?? [],
			recent_loops: summary.recent_loops ?? [],
			generated_at: new Date().toISOString(),
		});
	} catch (err) {
		return json({ error: err instanceof Error ? err.message : String(err) }, 500);
	}
});

function json(body: unknown, status = 200): Response {
	return new Response(JSON.stringify(body), {
		status,
		headers: { ...corsHeaders, "Content-Type": "application/json" },
	});
}