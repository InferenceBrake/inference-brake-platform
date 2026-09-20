import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { PLANS, isPlanId, planPriceId } from "../_shared/plans.ts";

const corsHeaders = {
	"Access-Control-Allow-Origin": "*",
	"Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

Deno.serve(async (req) => {
	if (req.method === "OPTIONS") {
		return new Response("ok", { headers: corsHeaders });
	}

	try {
		const authHeader = req.headers.get("Authorization");
		const apiKey = authHeader?.replace("Bearer ", "");

		if (!apiKey) {
			return json({ error: "Missing API key" }, 401);
		}

		const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
		const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

		const userRes = await fetch(
			`${supabaseUrl}/rest/v1/users?api_key=eq.${apiKey}&select=*`,
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

		const { plan } = await req.json();

		if (!isPlanId(plan)) {
			return json({ error: "Invalid plan" }, 400);
		}

		const planConfig = PLANS[plan];
		const isDemoMode = Deno.env.get("DEMO_MODE") === "true";
		const stripeKey = Deno.env.get("STRIPE_SECRET_KEY");

		// Free plan has no checkout flow.
		if (planConfig.priceUsd === 0) {
			return json({ error: "The Free plan does not require checkout." }, 400);
		}

		if (!stripeKey && !isDemoMode) {
			return json(
				{ error: "Payments not configured. Set STRIPE_SECRET_KEY." },
				503,
			);
		}

		// Demo mode - only when explicitly enabled, and only without a real key.
		if (!stripeKey && isDemoMode) {
			await fetch(`${supabaseUrl}/rest/v1/users?id=eq.${user.id}`, {
				method: "PATCH",
				headers: {
					apikey: supabaseKey,
					Authorization: `Bearer ${supabaseKey}`,
					"Content-Type": "application/json",
					Prefer: "return=minimal",
				},
				body: JSON.stringify({
					plan,
					monthly_limit: planConfig.monthlyLimit,
					subscription_status: "active",
				}),
			});

			return json({
				success: true,
				demo: true,
				message: "Demo mode - plan updated without payment",
				plan,
			});
		}

		const priceId = planPriceId(plan);
		if (!priceId) {
			return json(
				{
					error:
						`No Stripe price configured for the ${planConfig.name} plan. ` +
						`Set ${planConfig.priceEnv}.`,
				},
				503,
			);
		}

		const siteUrl = Deno.env.get("PUBLIC_SITE_URL") || "http://localhost:5173";
		const params = new URLSearchParams();
		params.append("mode", "subscription");
		params.append("success_url", `${siteUrl}/dashboard?success=true`);
		params.append("cancel_url", `${siteUrl}/dashboard?canceled=true`);
		params.append("line_items[0][price]", priceId);
		params.append("line_items[0][quantity]", "1");
		params.append("metadata[user_id]", user.id);
		params.append("metadata[plan]", plan);
		params.append("subscription_data[metadata][user_id]", user.id);
		params.append("subscription_data[metadata][plan]", plan);

		// Reuse the existing Stripe customer when available so upgrades and the
		// billing portal share one customer record.
		if (user.stripe_customer_id) {
			params.append("customer", user.stripe_customer_id);
		} else {
			params.append("customer_email", user.email);
		}

		const stripeRes = await fetch("https://api.stripe.com/v1/checkout/sessions", {
			method: "POST",
			headers: {
				Authorization: `Bearer ${stripeKey}`,
				"Content-Type": "application/x-www-form-urlencoded",
			},
			body: params,
		});

		const session = await stripeRes.json();

		if (session.error) {
			return json({ error: session.error.message }, 400);
		}

		if (session.customer && session.customer !== user.stripe_customer_id) {
			await fetch(`${supabaseUrl}/rest/v1/users?id=eq.${user.id}`, {
				method: "PATCH",
				headers: {
					apikey: supabaseKey,
					Authorization: `Bearer ${supabaseKey}`,
					"Content-Type": "application/json",
					Prefer: "return=minimal",
				},
				body: JSON.stringify({ stripe_customer_id: session.customer }),
			});
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