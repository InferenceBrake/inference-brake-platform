import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { PLANS, FREE_PLAN, planForPriceId, type PlanId } from "../_shared/plans.ts";

const corsHeaders = {
	"Access-Control-Allow-Origin": "*",
	"Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

// Reconciles the local user record with the current Stripe subscription.
// Called from the dashboard after a successful checkout so the plan updates
// immediately even if the webhook is delayed or not configured.
Deno.serve(async (req) => {
	if (req.method === "OPTIONS") {
		return new Response("ok", { headers: corsHeaders });
	}

	try {
		const apiKey = req.headers.get("Authorization")?.replace("Bearer ", "");
		if (!apiKey) {
			return json({ error: "Missing API key" }, 401);
		}

		const stripeKey = Deno.env.get("STRIPE_SECRET_KEY");
		if (!stripeKey) {
			return json({ error: "Payments not configured. Set STRIPE_SECRET_KEY." }, 503);
		}

		const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
		const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
		const stripeHeaders = { Authorization: `Bearer ${stripeKey}` };

		const userRes = await fetch(
			`${supabaseUrl}/rest/v1/users?api_key=eq.${apiKey}&select=id,email,plan,stripe_customer_id`,
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

		// Resolve the Stripe customer, falling back to an email lookup.
		let customerId: string | null = user.stripe_customer_id;
		if (!customerId && user.email) {
			const custRes = await fetch(
				`https://api.stripe.com/v1/customers?email=${encodeURIComponent(user.email)}&limit=1`,
				{ headers: stripeHeaders },
			);
			const customers = await custRes.json();
			customerId = customers.data?.[0]?.id ?? null;
		}

		if (!customerId) {
			return json({
				synced: false,
				plan: user.plan ?? FREE_PLAN,
				subscription_status: "inactive",
			});
		}

		const subsRes = await fetch(
			`https://api.stripe.com/v1/subscriptions?customer=${customerId}&status=all&limit=10`,
			{ headers: stripeHeaders },
		);
		const subs = await subsRes.json();

		const sub = (subs.data ?? []).find((s: { status: string }) =>
			["active", "trialing", "past_due"].includes(s.status)
		) ?? (subs.data ?? [])[0];

		let plan: PlanId = user.plan ?? FREE_PLAN;
		let subscriptionStatus = "inactive";
		let subscriptionId: string | null = null;
		let periodEnd: string | null = null;

		if (sub) {
			subscriptionId = sub.id;
			const priceId = sub.items?.data?.[0]?.price?.id;
			const cfg = planForPriceId(priceId);
			// Only change the plan when the price is recognized; never silently
			// downgrade a user whose price is not in the current config.
			if (cfg) plan = cfg.id;

			if (sub.status === "past_due" || sub.status === "unpaid") {
				subscriptionStatus = "past_due";
			} else if (sub.status === "active" || sub.status === "trialing") {
				subscriptionStatus = "active";
			} else {
				subscriptionStatus = "canceled";
				plan = FREE_PLAN;
			}

			if (sub.current_period_end) {
				periodEnd = new Date(sub.current_period_end * 1000).toISOString();
			}
		}

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
				daily_limit: PLANS[plan].dailyLimit,
				subscription_status: subscriptionStatus,
				stripe_customer_id: customerId,
				stripe_subscription_id: subscriptionId,
				subscription_current_period_end: periodEnd,
			}),
		});

		return json({
			synced: true,
			plan,
			subscription_status: subscriptionStatus,
			daily_limit: PLANS[plan].dailyLimit,
			subscription_current_period_end: periodEnd,
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