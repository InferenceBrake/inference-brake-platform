import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface PlanConfig {
  priceId: string;
  name: string;
  dailyLimit: number;
}

const PLANS: Record<string, PlanConfig> = {
  hobby: {
    priceId: "",
    name: "Hobby",
    dailyLimit: 1000,
  },
  pro: {
    priceId: Deno.env.get("STRIPE_PRO_PRICE_ID") || "price_pro",
    name: "Pro",
    dailyLimit: 10000,
  },
};

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  // Beta mode: payments not yet enabled
  return new Response(JSON.stringify({ 
    error: "Payments not yet enabled. Join the waitlist to be notified when Pro launches.",
    beta: true
  }), {
    status: 503,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });

  try {
    const authHeader = req.headers.get("Authorization");
    const apiKey = authHeader?.replace("Bearer ", "");
    
    if (!apiKey) {
      return new Response(JSON.stringify({ error: "Missing API key" }), {
        status: 401,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // Get user from API key
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

    const { plan } = await req.json();
    const planConfig = PLANS[plan];
    
    if (!planConfig) {
      return new Response(JSON.stringify({ error: "Invalid plan" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const isDemoMode = Deno.env.get("DEMO_MODE") === "true";
    const stripeKey = Deno.env.get("STRIPE_SECRET_KEY");

    // If no Stripe key and not in demo mode, reject upgrade
    if (!stripeKey && !isDemoMode) {
      return new Response(JSON.stringify({ error: "Payments not configured. Please contact support." }), {
        status: 503,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // Demo mode - only allow if explicitly enabled
    if (!stripeKey && isDemoMode) {
      await fetch(`${supabaseUrl}/rest/v1/users?id=eq.${user.id}`, {
        method: "PATCH",
        headers: {
          "apikey": supabaseKey,
          "Authorization": `Bearer ${supabaseKey}`,
          "Content-Type": "application/json",
          "Prefer": "return=minimal",
        },
        body: JSON.stringify({
          plan: plan,
          daily_limit: planConfig.dailyLimit,
          subscription_status: "active",
        }),
      });
      
      return new Response(JSON.stringify({
        success: true,
        demo: true,
        message: "Demo mode - plan updated without payment",
        plan: plan,
      }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // Create Stripe checkout session
    const stripeUrl = "https://api.stripe.com/v1/checkout/sessions";
    const params = new URLSearchParams();
    params.append("mode", "subscription");
    params.append("customer_email", user.email);
    params.append("success_url", `${Deno.env.get("PUBLIC_SITE_URL") || "http://localhost:5173"}/dashboard?success=true`);
    params.append("cancel_url", `${Deno.env.get("PUBLIC_SITE_URL") || "http://localhost:5173"}/dashboard?canceled=true`);
    params.append("line_items[0][price]", planConfig.priceId);
    params.append("line_items[0][quantity]", "1");
    params.append("metadata[user_id]", user.id);
    params.append("metadata[plan]", plan);

    const stripeRes = await fetch(stripeUrl, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${stripeKey}`,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: params,
    });

    const session = await stripeRes.json();

    if (session.error) {
      return new Response(JSON.stringify({ error: session.error.message }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // Store Stripe customer ID if provided
    if (session.customer) {
      await fetch(`${supabaseUrl}/rest/v1/users?id=eq.${user.id}`, {
        method: "PATCH",
        headers: {
          "apikey": supabaseKey,
          "Authorization": `Bearer ${supabaseKey}`,
          "Content-Type": "application/json",
          "Prefer": "return=minimal",
        },
        body: JSON.stringify({
          stripe_customer_id: session.customer,
        }),
      });
    }

    return new Response(JSON.stringify({
      url: session.url,
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
