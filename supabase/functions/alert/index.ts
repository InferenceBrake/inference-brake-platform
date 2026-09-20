import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import {
	buildAlertHtml,
	buildAlertText,
	buildSlackMessage,
	emailConfigured,
	sendEmail,
	sendSlack,
	type AlertPayload,
} from "../_shared/alerts.ts";

const corsHeaders = {
	"Access-Control-Allow-Origin": "*",
	"Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

// Multi-channel alert dispatcher. Sends a loop alert to the user's configured
// email and/or webhook, or to destinations provided in the request body.
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
			`${supabaseUrl}/rest/v1/users?api_key=eq.${apiKey}&select=id,email,alert_email,webhook_url`,
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

		const body = await req.json().catch(() => ({}));
		const payload: AlertPayload = body.payload ?? body;
		const text = buildAlertText(payload);
		const html = buildAlertHtml(payload);
		const slack = buildSlackMessage(payload);

		const results: Record<string, { ok: boolean; error?: string }> = {};

		const to: string | undefined = body.email ?? user.alert_email;
		if (to) {
			const config = emailConfigured();
			if (!config) {
				results.email = { ok: false, error: "Email not configured (set RESEND_API_KEY and ALERT_FROM_EMAIL)" };
			} else {
				results.email = await sendEmail({
					apiKey: config.apiKey,
					from: config.from,
					to,
					subject: "InferenceBrake: loop detected and halted",
					text,
					html,
				});
			}
		}

		const webhookUrl: string | undefined = body.webhook_url ?? user.webhook_url;
		if (webhookUrl) {
			results.slack = await sendSlack(webhookUrl, slack.text, slack.blocks);
		}

		if (Object.keys(results).length === 0) {
			return json({ error: "No alert destination configured" }, 400);
		}

		const ok = Object.values(results).every((r) => r.ok);
		return json({ ok, results, text }, ok ? 200 : 502);
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
