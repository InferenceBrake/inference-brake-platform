import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const { session_id, reasoning, similarity, detectors, action, webhook_url, message } = await req.json();

    if (!webhook_url) {
      return new Response(JSON.stringify({ error: "Missing webhook_url" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const slackMessage = {
      text: "InferenceBrake Alert: Loop Detected",
      blocks: [
        {
          type: "header",
          text: {
            type: "plain_text",
            text: "InferenceBrake Alert",
            emoji: true
          }
        },
        {
          type: "section",
          fields: [
            {
              type: "mrkdwn",
              text: `*Action:*\n${action || "KILL"}`
            },
            {
              type: "mrkdwn",
              text: `*Similarity:*\n${similarity ? (similarity * 100).toFixed(1) + "%" : "N/A"}`
            }
          ]
        },
        {
          type: "section",
          text: {
            type: "mrkdwn",
            text: `*Reasoning:*\n${(reasoning || "").substring(0, 500)}`
          }
        },
        {
          type: "section",
          fields: [
            {
              type: "mrkdwn",
              text: `*Detectors:*\n${detectors ? Object.entries(detectors).filter(([_, v]) => v).map(([k]) => k).join(", ") || "None" : "N/A"}`
            },
            {
              type: "mrkdwn",
              text: `*Session:*\n${session_id || "Unknown"}`
            }
          ]
        },
        {
          type: "context",
          elements: [
            {
              type: "mrkdwn",
              text: message || "A reasoning loop was detected and blocked."
            }
          ]
        }
      ]
    };

    const response = await fetch(webhook_url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(slackMessage),
    });

    if (!response.ok) {
      const errorText = await response.text();
      return new Response(JSON.stringify({ error: "Failed to send Slack notification", details: errorText }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    return new Response(JSON.stringify({
      success: true,
      message: "Slack notification sent",
    }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });

  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
