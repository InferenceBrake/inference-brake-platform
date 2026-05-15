import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const corsHeaders = {
	"Access-Control-Allow-Origin": "*",
	"Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

Deno.serve(async (req) => {
	if (req.method === "OPTIONS")
		return new Response("ok", { headers: corsHeaders });

	try {
		const authHeader = req.headers.get("Authorization");
		const jwt = authHeader?.replace("Bearer ", "");

		if (!jwt) {
			return new Response(JSON.stringify({ error: "Missing authorization" }), {
				status: 401,
				headers: { ...corsHeaders, "Content-Type": "application/json" },
			});
		}

		const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
		const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
		const supabase = createClient(supabaseUrl, supabaseKey);

		// Verify the JWT and get the user
		const { data: { user }, error: authError } = await supabase.auth.getUser(jwt);
		if (authError || !user) {
			return new Response(JSON.stringify({ error: "Invalid session" }), {
				status: 401,
				headers: { ...corsHeaders, "Content-Type": "application/json" },
			});
		}

		// Look up existing API key
		const { data: existing } = await supabase
			.from("users")
			.select("api_key")
			.eq("id", user.id)
			.single();

		if (existing?.api_key) {
			return new Response(JSON.stringify({ api_key: existing.api_key }), {
				headers: { ...corsHeaders, "Content-Type": "application/json" },
			});
		}

		// Generate a new key if none exists
		const randomBytes = new Uint8Array(32);
		crypto.getRandomValues(randomBytes);
		const newKey = "ib_" + Array.from(randomBytes)
			.map((b) => b.toString(16).padStart(2, "0"))
			.join("");

		await supabase
			.from("users")
			.update({ api_key: newKey, updated_at: new Date().toISOString() })
			.eq("id", user.id);

		return new Response(JSON.stringify({ api_key: newKey }), {
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	} catch (err) {
		return new Response(JSON.stringify({ error: err.message }), {
			status: 500,
			headers: { ...corsHeaders, "Content-Type": "application/json" },
		});
	}
});
