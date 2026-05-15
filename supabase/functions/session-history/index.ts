import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const supabase = createClient(
	Deno.env.get("SUPABASE_URL")!,
	Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

const corsHeaders = {
	"Access-Control-Allow-Origin": "*",
	"Access-Control-Allow-Headers":
		"authorization, x-client-info, apikey, content-type",
};

Deno.serve(async (req) => {
	if (req.method === "OPTIONS")
		return new Response("ok", { headers: corsHeaders });

	try {
		const authHeader = req.headers.get("Authorization");
		const apiKey = authHeader?.replace("Bearer ", "");
		if (!apiKey)
			return new Response(JSON.stringify({ error: "Missing API Key" }), {
				status: 401,
				headers: { ...corsHeaders, "Content-Type": "application/json" },
			});

		const { data: user, error: authError } = await supabase
			.from("users")
			.select("id")
			.or(`api_key.eq.${apiKey},test_mode_api_key.eq.${apiKey}`)
			.single();

		if (authError || !user)
			return new Response(JSON.stringify({ error: "Invalid API Key" }), {
				status: 401,
				headers: { ...corsHeaders, "Content-Type": "application/json" },
			});

		const url = new URL(req.url);
		const sessionId = url.searchParams.get("session_id");
		const limit = parseInt(url.searchParams.get("limit") || "50", 10);
		const offset = parseInt(url.searchParams.get("offset") || "0", 10);

		if (!sessionId)
			return new Response(JSON.stringify({ error: "Missing session_id" }), {
				status: 400,
				headers: { ...corsHeaders, "Content-Type": "application/json" },
			});

		const { data: steps, error: stepsError, count } = await supabase
			.from("reasoning_history")
			.select("step_number, reasoning, action, loop_detected, similarity, created_at", { count: "exact" })
			.eq("session_id", sessionId)
			.eq("user_id", user.id)
			.order("step_number", { ascending: true })
			.range(offset, offset + limit - 1);

		if (stepsError)
			return new Response(JSON.stringify({ error: stepsError.message }), {
				status: 500,
				headers: { ...corsHeaders, "Content-Type": "application/json" },
			});

		return new Response(
			JSON.stringify({
				session_id: sessionId,
				steps: steps || [],
				total: count || 0,
				limit,
				offset,
			}),
			{
				headers: { ...corsHeaders, "Content-Type": "application/json" },
			},
		);
	} catch (err) {
		return new Response(JSON.stringify({ error: err.message }), {
			status: 500,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}
});
