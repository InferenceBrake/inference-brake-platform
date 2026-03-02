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

    const userId = user.id;

    await fetch(`${supabaseUrl}/rest/v1/reasoning_history?user_id=eq.${userId}`, {
      method: "DELETE",
      headers: {
        "apikey": supabaseKey,
        "Authorization": `Bearer ${supabaseKey}`,
      },
    });

    await fetch(`${supabaseUrl}/rest/v1/metrics?user_id=eq.${userId}`, {
      method: "DELETE",
      headers: {
        "apikey": supabaseKey,
        "Authorization": `Bearer ${supabaseKey}`,
      },
    });

    await fetch(`${supabaseUrl}/rest/v1/users?id=eq.${userId}`, {
      method: "DELETE",
      headers: {
        "apikey": supabaseKey,
        "Authorization": `Bearer ${supabaseKey}`,
      },
    });

    const authRes = await fetch(`${supabaseUrl}/auth/v1/admin/users/${userId}`, {
      method: "DELETE",
      headers: {
        "Authorization": `Bearer ${supabaseKey}`,
        "apikey": supabaseKey,
      },
    });

    return new Response(JSON.stringify({
      success: true,
      message: "Account deleted successfully",
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
