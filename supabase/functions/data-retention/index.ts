import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const supabase = createClient(
	Deno.env.get("SUPABASE_URL")!,
	Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

const cronSecret = Deno.env.get("CRON_SECRET");

Deno.serve(async (req) => {
	// Accept both x-cron-secret (custom) and x-cron-job (Supabase standard)
	const incomingSecret = req.headers.get("x-cron-secret") || req.headers.get("x-cron-job");
	if (!cronSecret || incomingSecret !== cronSecret) {
		return new Response(JSON.stringify({ error: "Unauthorized" }), { status: 401 });
	}

	const corsHeaders = {
		"Access-Control-Allow-Origin": "*",
		"Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
	};

	if (req.method === "OPTIONS") {
		return new Response("ok", { headers: corsHeaders });
	}

	try {
		// Call the database function for data retention cleanup
		const { data, error } = await supabase.rpc("cleanup_old_sessions");

		if (error) {
			console.error("Data retention error:", error);
			return new Response(JSON.stringify({ error: error.message }), {
				status: 500,
				headers: { ...corsHeaders, "Content-Type": "application/json" },
			});
		}

		return new Response(JSON.stringify({ 
			success: true, 
			message: "Data retention cleanup completed",
			result: data 
		}), {
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	} catch (err) {
		console.error("Cron error:", err);
		return new Response(JSON.stringify({ error: err.message }), {
			status: 500,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}
});
