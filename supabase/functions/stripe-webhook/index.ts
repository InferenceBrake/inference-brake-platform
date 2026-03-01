import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, stripe-signature",
};

const PLANS: Record<string, { dailyLimit: number }> = {
  hobby: { dailyLimit: 1000 },
  pro: { dailyLimit: 10000 },
};

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const stripeKey = Deno.env.get("STRIPE_SECRET_KEY");
    const webhookSecret = Deno.env.get("STRIPE_WEBHOOK_SECRET");
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

    if (!stripeKey || !webhookSecret) {
      return new Response(JSON.stringify({ error: "Stripe not configured" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const signature = req.headers.get("stripe-signature");
    const body = await req.text();

    if (!signature) {
      return new Response(JSON.stringify({ error: "Missing stripe-signature header" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const sigParts = signature.split(",").reduce((acc: Record<string, string>, part) => {
      const [key, value] = part.split("=");
      if (key && value) acc[key] = value;
      return acc;
    }, {});

    const timestamp = sigParts.t;
    const receivedSignature = sigParts.v1;

    if (!timestamp || !receivedSignature) {
      return new Response(JSON.stringify({ error: "Invalid signature format" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const timestampNum = parseInt(timestamp, 10);
    const now = Math.floor(Date.now() / 1000);
    if (now - timestampNum > 300) {
      return new Response(JSON.stringify({ error: "Webhook timestamp too old" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const signedPayload = `${timestamp}.${body}`;
    const encoder = new TextEncoder();
    const key = await crypto.subtle.importKey(
      "raw",
      encoder.encode(webhookSecret),
      { name: "HMAC", hash: "SHA-256" },
      false,
      ["sign"]
    );
    const signatureBytes = await crypto.subtle.sign("HMAC", key, encoder.encode(signedPayload));
    const expectedSignature = Array.from(new Uint8Array(signatureBytes))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');

    let cryptoOk = false;
    try {
      if (expectedSignature.length === receivedSignature.length) {
        cryptoOk = crypto.subtle.timingSafeEqual(
          encoder.encode(expectedSignature),
          encoder.encode(receivedSignature)
        );
      }
    } catch {
      cryptoOk = false;
    }

    if (!cryptoOk) {
      return new Response(JSON.stringify({ error: "Invalid signature" }), {
        status: 401,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const event = JSON.parse(body);
    const data = event.data.object;
    const userId = data.metadata?.user_id;

    if (!userId) {
      return new Response(JSON.stringify({ error: "No user_id in metadata" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    let updateData: Record<string, unknown> = {};

    switch (event.type) {
      case "checkout.session.completed": {
        const subscriptionId = data.subscription;
        const customerId = data.customer;
        
        // Get subscription details to determine plan
        const subRes = await fetch(`https://api.stripe.com/v1/subscriptions/${subscriptionId}`, {
          headers: { "Authorization": `Bearer ${stripeKey}` },
        });
        const subscription = await subRes.json();
        
        const priceId = subscription.items?.data?.[0]?.price?.id;
        let plan = "hobby";
        let dailyLimit = 1000;
        
        const proPriceId = Deno.env.get("STRIPE_PRO_PRICE_ID");
        if (priceId === proPriceId) {
          plan = "pro";
          dailyLimit = 10000;
        }

        updateData = {
          stripe_subscription_id: subscriptionId,
          stripe_customer_id: customerId,
          plan: plan,
          daily_limit: dailyLimit,
          subscription_status: "active",
          subscription_current_period_end: new Date(subscription.current_period_end * 1000).toISOString(),
        };
        break;
      }

      case "customer.subscription.updated": {
        const status = data.status;
        const currentPeriodEnd = new Date(data.current_period_end * 1000).toISOString();
        
        let subscriptionStatus = "active";
        if (status === "past_due" || status === "unpaid") {
          subscriptionStatus = "past_due";
        } else if (status === "canceled" || status === "unended") {
          subscriptionStatus = "canceled";
        }

        updateData = {
          subscription_status: subscriptionStatus,
          subscription_current_period_end: currentPeriodEnd,
        };
        break;
      }

      case "customer.subscription.deleted": {
        updateData = {
          plan: "hobby",
          daily_limit: 1000,
          subscription_status: "canceled",
          stripe_subscription_id: null,
        };
        break;
      }

      case "invoice.payment_failed": {
        updateData = {
          subscription_status: "past_due",
        };
        break;
      }

      default:
        console.log(`Unhandled event type: ${event.type}`);
    }

    // Update user in database
    if (Object.keys(updateData).length > 0) {
      await fetch(`${supabaseUrl}/rest/v1/users?id=eq.${userId}`, {
        method: "PATCH",
        headers: {
          "apikey": supabaseKey,
          "Authorization": `Bearer ${supabaseKey}`,
          "Content-Type": "application/json",
          "Prefer": "return=minimal",
        },
        body: JSON.stringify(updateData),
      });
    }

    return new Response(JSON.stringify({ received: true }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });

  } catch (err) {
    console.error("Webhook error:", err);
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
