// Shared plan definitions for Stripe billing.
//
// Quota enforcement is monthly (users.checks_this_month / users.monthly_limit),
// reset by pg_cron on the 1st. Stripe price IDs come from environment variables
// so no secret material is committed.

export type PlanId = "hobby" | "growth" | "pro";

export interface PlanConfig {
	id: PlanId;
	name: string;
	priceUsd: number;
	monthlyLimit: number;
	priceEnv: string | null;
	features: string[];
}

export const PLANS: Record<PlanId, PlanConfig> = {
	hobby: {
		id: "hobby",
		name: "Free",
		priceUsd: 0,
		monthlyLimit: 5000,
		priceEnv: null,
		features: [
			"All 6 detectors",
			"5,000 checks/month",
			"7-day log retention",
			"Email support",
		],
	},
	growth: {
		id: "growth",
		name: "Growth",
		priceUsd: 49,
		monthlyLimit: 100000,
		priceEnv: "STRIPE_GROWTH_PRICE_ID",
		features: [
			"All 6 detectors",
			"100,000 checks/month",
			"Slack + webhook alerts",
			"Est. dollars-saved dashboard",
			"30-day log retention",
		],
	},
	pro: {
		id: "pro",
		name: "Pro",
		priceUsd: 199,
		monthlyLimit: 500000,
		priceEnv: "STRIPE_PRO_PRICE_ID",
		features: [
			"All 6 detectors",
			"500,000 checks/month",
			"Custom voting thresholds",
			"Priority API latency",
			"90-day log retention",
		],
	},
};

export const FREE_PLAN: PlanId = "hobby";

export function isPlanId(value: unknown): value is PlanId {
	return typeof value === "string" && value in PLANS;
}

export function planForPriceId(priceId: string | null | undefined): PlanConfig | null {
	if (!priceId) return null;
	for (const plan of Object.values(PLANS)) {
		if (plan.priceEnv && Deno.env.get(plan.priceEnv) === priceId) return plan;
	}
	return null;
}

export function planPriceId(plan: PlanId): string | null {
	const cfg = PLANS[plan];
	if (!cfg.priceEnv) return null;
	return Deno.env.get(cfg.priceEnv) ?? null;
}
