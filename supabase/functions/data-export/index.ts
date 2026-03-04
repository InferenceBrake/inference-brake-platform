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
    
    const userRes = await fetch(`${supabaseUrl}/rest/v1/users?api_key=eq.${apiKey}&select=id,email`, {
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

    const userId = user.id;

    const [historyRes, metricsRes, accountRes] = await Promise.all([
      fetch(`${supabaseUrl}/rest/v1/reasoning_history?user_id=eq.${userId}&select=*`, {
        headers: {
          "apikey": supabaseKey,
          "Authorization": `Bearer ${supabaseKey}`,
        },
      }),
      fetch(`${supabaseUrl}/rest/v1/metrics?user_id=eq.${userId}&select=*`, {
        headers: {
          "apikey": supabaseKey,
          "Authorization": `Bearer ${supabaseKey}`,
        },
      }),
      fetch(`${supabaseUrl}/rest/v1/users?id=eq.${userId}&select=*`, {
        headers: {
          "apikey": supabaseKey,
          "Authorization": `Bearer ${supabaseKey}`,
        },
      }),
    ]);

    const history = await historyRes.json();
    const metrics = await metricsRes.json();
    const accountData = await accountRes.json();

    const exportData = {
      exported_at: new Date().toISOString(),
      user: {
        email: user.email,
        plan: accountData[0]?.plan,
        created_at: accountData[0]?.created_at,
      },
      data_retention: {
        hobby: "7 days",
        pro: "90 days",
      },
      reasoning_history: history,
      metrics: metrics,
      total_records: {
        reasoning_history: history.length,
        metrics: metrics.length,
      },
    };

    return new Response(JSON.stringify(exportData, null, 2), {
      headers: { 
        ...corsHeaders, 
        "Content-Type": "application/json",
        "Content-Disposition": `attachment; filename="inferencebrake-export-${userId}.json"`,
      },
    });

  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
