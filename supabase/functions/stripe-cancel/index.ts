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
    const authHeader = req.headers.get("Authorization");
    const apiKey = authHeader?.replace("Bearer ", "");
    
    if (!apiKey) {
      return new Response(JSON.stringify({ error: "Missing API key" }), {
        status: 401,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    
    const userRes = await fetch(`${supabaseUrl}/rest/v1/users?api_key=eq.${apiKey}&select=*`, {
      headers: {
        "apikey": supabaseKey,
        "Authorization": `Bearer ${supabaseKey}`,
      },
    });
    
    const users = await userRes.json();
    const user = users[0];
    
    if (!user) {
      return new Response(JSON.stringify({ error: "Invalid API key" }), {
        status: 401,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    if (!user.stripe_subscription_id) {
      return new Response(JSON.stringify({ error: "No active subscription" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const stripeKey = Deno.env.get("STRIPE_SECRET_KEY");
    if (!stripeKey) {
      await fetch(`${supabaseUrl}/rest/v1/users?id=eq.${user.id}`, {
        method: "PATCH",
        headers: {
          "apikey": supabaseKey,
          "Authorization": `Bearer ${supabaseKey}`,
          "Content-Type": "application/json",
          "Prefer": "return=minimal",
        },
        body: JSON.stringify({
          plan: "hobby",
          daily_limit: 1000,
          subscription_status: "canceled",
          stripe_subscription_id: null,
        }),
      });
      
      return new Response(JSON.stringify({
        success: true,
        demo: true,
        message: "Demo mode - subscription canceled",
      }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const stripeRes = await fetch(
      `https://api.stripe.com/v1/subscriptions/${user.stripe_subscription_id}`,
      {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${stripeKey}`,
          "Content-Type": "application/x-www-form-urlencoded",
        },
      }
    );

    if (!stripeRes.ok) {
      const error = await stripeRes.json();
      return new Response(JSON.stringify({ error: error.error?.message || "Failed to cancel subscription" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    await fetch(`${supabaseUrl}/rest/v1/users?id=eq.${user.id}`, {
      method: "PATCH",
      headers: {
        "apikey": supabaseKey,
        "Authorization": `Bearer ${supabaseKey}`,
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
      },
      body: JSON.stringify({
        plan: "hobby",
        daily_limit: 1000,
        subscription_status: "canceled",
        stripe_subscription_id: null,
      }),
    });

    return new Response(JSON.stringify({
      success: true,
      message: "Subscription canceled successfully",
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
