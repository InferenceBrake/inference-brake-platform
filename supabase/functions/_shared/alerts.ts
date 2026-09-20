// Shared alert helpers for loop notifications (email via Resend, Slack/generic
// webhook). Used by the alert edge function and by check for auto-dispatch.

const DASHBOARD_URL = "https://www.inferencebrake.dev/dashboard";

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

function confidencePct(payload: AlertPayload): string {
	return payload.confidence != null ? `${(payload.confidence * 100).toFixed(0)}%` : "n/a";
}

function savedUsd(payload: AlertPayload): string {
	return `$${(payload.estimated_cost_saved ?? 0).toFixed(4)}`;
}

export function buildAlertText(payload: AlertPayload): string {
	const lines = [
		"InferenceBrake: loop detected and halted",
		`Session: ${payload.session_id ?? "unknown"}`,
		`Model: ${payload.model ?? "unknown"}`,
		`Action: ${payload.action ?? "unknown"}`,
		`Confidence: ${confidencePct(payload)}`,
		`Detectors: ${firedDetectors(payload.detectors)}`,
		`Estimated saved: ${savedUsd(payload)}`,
	];
	if (payload.reasoning) {
		lines.push(`Reasoning: ${payload.reasoning.slice(0, 300)}`);
	}
	lines.push(`Dashboard: ${DASHBOARD_URL}`);
	return lines.join("\n");
}

function escapeHtml(value: string): string {
	return value
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;");
}

export function buildAlertHtml(payload: AlertPayload): string {
	const row = (label: string, value: string) =>
		`<tr>
			<td style="padding:6px 0;color:#71717a;font-size:13px;width:120px;">${label}</td>
			<td style="padding:6px 0;color:#e5e5e7;font-size:13px;">${escapeHtml(value)}</td>
		</tr>`;

	const reasoning = payload.reasoning
		? `<tr><td colspan="2" style="padding:14px 0 0 0;">
				<div style="color:#71717a;font-size:13px;margin-bottom:6px;">Reasoning</div>
				<div style="background:#0b0b0c;border:1px solid #26262b;border-radius:8px;padding:12px;color:#a1a1aa;font-size:13px;line-height:1.6;">${escapeHtml(payload.reasoning.slice(0, 400))}</div>
			</td></tr>`
		: "";

	return `<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Loop detected</title></head>
<body style="margin:0;padding:0;background-color:#0b0b0c;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#0b0b0c;padding:32px 16px;">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px;background-color:#141416;border:1px solid #26262b;border-radius:12px;">
        <tr><td style="padding:28px 32px 0 32px;">
          <span style="font-size:18px;font-weight:700;color:#f97316;letter-spacing:-0.01em;">InferenceBrake</span>
        </td></tr>
        <tr><td style="padding:16px 32px 0 32px;color:#e5e5e7;font-size:20px;font-weight:600;">
          Loop detected and halted
        </td></tr>
        <tr><td style="padding:12px 32px 0 32px;color:#a1a1aa;font-size:14px;line-height:1.6;">
          An agent loop was detected and stopped before it burned more budget.
        </td></tr>
        <tr><td style="padding:18px 32px 0 32px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
            ${row("Session", payload.session_id ?? "unknown")}
            ${row("Model", payload.model ?? "unknown")}
            ${row("Action", payload.action ?? "unknown")}
            ${row("Confidence", confidencePct(payload))}
            ${row("Detectors", firedDetectors(payload.detectors))}
            ${row("Estimated saved", savedUsd(payload))}
            ${reasoning}
          </table>
        </td></tr>
        <tr><td style="padding:24px 32px 8px 32px;">
          <a href="${DASHBOARD_URL}" style="display:inline-block;background-color:#f97316;color:#ffffff;text-decoration:none;font-weight:600;font-size:14px;padding:12px 20px;border-radius:8px;">Open dashboard</a>
        </td></tr>
        <tr><td style="padding:20px 32px 28px 32px;color:#71717a;font-size:12px;line-height:1.6;border-top:1px solid #26262b;">
          Alerts fire once per session. Manage destinations in Settings, Alerts.
          <br><br>
          <a href="https://www.inferencebrake.dev" style="color:#a1a1aa;text-decoration:none;">inferencebrake.dev</a>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>`;
}

export function buildSlackMessage(payload: AlertPayload): { text: string; blocks: unknown[] } {
	const field = (label: string, value: string) => ({ type: "mrkdwn", text: `*${label}*\n${value}` });

	const blocks: unknown[] = [
		{
			type: "header",
			text: { type: "plain_text", text: "Loop detected and halted", emoji: true },
		},
		{
			type: "section",
			fields: [
				field("Session", payload.session_id ?? "unknown"),
				field("Confidence", confidencePct(payload)),
				field("Model", payload.model ?? "unknown"),
				field("Tool", payload.action ?? "unknown"),
				field("Detectors", firedDetectors(payload.detectors)),
				field("Est. saved", savedUsd(payload)),
			],
		},
	];

	if (payload.reasoning) {
		blocks.push({
			type: "section",
			text: { type: "mrkdwn", text: `*Reasoning*\n>${payload.reasoning.slice(0, 400)}` },
		});
	}

	blocks.push({
		type: "context",
		elements: [{ type: "mrkdwn", text: `<${DASHBOARD_URL}|Open dashboard>` }],
	});

	return { text: `InferenceBrake: loop detected in ${payload.session_id ?? "unknown"}`, blocks };
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
	html?: string;
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
			...(opts.html ? { html: opts.html } : {}),
		}),
	});
	if (!res.ok) {
		return { ok: false, error: (await res.text()).slice(0, 300) };
	}
	return { ok: true };
}

export async function sendSlack(
	webhookUrl: string,
	text: string,
	blocks?: unknown[],
): Promise<SendResult> {
	// Slack renders Block Kit; other webhooks get the plain text.
	const isSlack = webhookUrl.includes("hooks.slack.com");
	const body = isSlack && blocks ? { text, blocks } : { text };

	const res = await fetch(webhookUrl, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(body),
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
