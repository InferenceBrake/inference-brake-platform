import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const corsHeaders = {
	"Access-Control-Allow-Origin": "*",
	"Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

// Creates a Stripe Billing Portal session so users can update payment methods,
// change plans, and cancel without custom UI.
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

		const userRes = await fetch(
			`${supabaseUrl}/rest/v1/users?api_key=eq.${apiKey}&select=id,stripe_customer_id`,
			{
				headers: {
					apikey: supabaseKey,
					Authorization: `Bearer ${supabaseKey}`,
				},
			},
		);

		const users = await userRes.json();
		const user = users[0];

		if (!user) {
			return json({ error: "Invalid API key" }, 401);
		}

		if (!user.stripe_customer_id) {
			return json({ error: "No billing account found. Subscribe first." }, 400);
		}

		const stripeKey = Deno.env.get("STRIPE_SECRET_KEY");
		if (!stripeKey) {
			return json(
				{ error: "Payments not configured. Set STRIPE_SECRET_KEY." },
				503,
			);
		}

		const siteUrl = Deno.env.get("PUBLIC_SITE_URL") || "http://localhost:5173";
		const params = new URLSearchParams();
		params.append("customer", user.stripe_customer_id);
		params.append("return_url", `${siteUrl}/settings`);

		const stripeRes = await fetch(
			"https://api.stripe.com/v1/billing_portal/sessions",
			{
				method: "POST",
				headers: {
					Authorization: `Bearer ${stripeKey}`,
					"Content-Type": "application/x-www-form-urlencoded",
				},
				body: params,
			},
		);

		const session = await stripeRes.json();

		if (session.error) {
			return json({ error: session.error.message }, 400);
		}

		return json({ url: session.url });
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