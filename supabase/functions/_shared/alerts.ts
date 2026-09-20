// Shared alert helpers for loop notifications (email via Resend, Slack/generic
// webhook). Used by the alert edge function and by check for auto-dispatch.

export interface AlertPayload {
	session_id?: string;
	reasoning?: string;
	similarity?: number;
	confidence?: number;
	detectors?: Record<string, boolean>;
	action?: string;
	model?: string | null;
	prompt?: string | null;
	estimated_cost_saved?: number;
	message?: string;
}

export function firedDetectors(detectors?: Record<string, boolean>): string {
	if (!detectors) return "none";
	const fired = Object.entries(detectors)
		.filter(([, value]) => value)
		.map(([name]) => name);
	return fired.length ? fired.join(", ") : "none";
}

export function buildAlertText(payload: AlertPayload): string {
	const confidence = payload.confidence != null
		? `${(payload.confidence * 100).toFixed(0)}%`
		: "n/a";
	const saved = (payload.estimated_cost_saved ?? 0).toFixed(4);

	const lines = [
		"InferenceBrake: loop detected and halted",
		`Session: ${payload.session_id ?? "unknown"}`,
		`Model: ${payload.model ?? "unknown"}`,
		`Action: ${payload.action ?? "unknown"}`,
		`Confidence: ${confidence}`,
		`Detectors: ${firedDetectors(payload.detectors)}`,
		`Estimated saved: $${saved}`,
	];

	if (payload.reasoning) {
		lines.push(`Reasoning: ${payload.reasoning.slice(0, 300)}`);
	}
	return lines.join("\n");
}

export interface SendResult {
	ok: boolean;
	error?: string;
}

export async function sendEmail(opts: {
	apiKey: string;
	from: string;
	to: string;
	subject: string;
	text: string;
}): Promise<SendResult> {
	const res = await fetch("https://api.resend.com/emails", {
		method: "POST",
		headers: {
			Authorization: `Bearer ${opts.apiKey}`,
			"Content-Type": "application/json",
		},
		body: JSON.stringify({
			from: opts.from,
			to: [opts.to],
			subject: opts.subject,
			text: opts.text,
		}),
	});
	if (!res.ok) {
		return { ok: false, error: (await res.text()).slice(0, 300) };
	}
	return { ok: true };
}

export async function sendSlack(webhookUrl: string, text: string): Promise<SendResult> {
	const res = await fetch(webhookUrl, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ text }),
	});
	if (!res.ok) {
		return { ok: false, error: (await res.text()).slice(0, 300) };
	}
	return { ok: true };
}

export function emailConfigured(): { apiKey: string; from: string } | null {
	const apiKey = Deno.env.get("RESEND_API_KEY");
	const from = Deno.env.get("ALERT_FROM_EMAIL");
	if (!apiKey || !from) return null;
	return { apiKey, from };
}
