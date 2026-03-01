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
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

    const dbStart = Date.now();
    const dbRes = await fetch(`${supabaseUrl}/rest/v1/`, {
      method: "HEAD",
      headers: {
        "apikey": supabaseKey,
        "Authorization": `Bearer ${supabaseKey}`,
      },
    });
    const dbLatency = Date.now() - dbStart;

    const status = dbRes.ok ? "healthy" : "degraded";
    const httpStatus = status === "healthy" ? 200 : 503;

    return new Response(JSON.stringify({
      status,
      timestamp: new Date().toISOString(),
      services: {
        database: {
          status: dbRes.ok ? "up" : "down",
          latency_ms: dbLatency,
        },
      },
      version: "1.0.0",
    }), {
      status: httpStatus,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });

  } catch (err) {
    return new Response(JSON.stringify({
      status: "unhealthy",
      timestamp: new Date().toISOString(),
      error: err.message,
    }), {
      status: 503,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
