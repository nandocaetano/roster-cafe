const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Content-Type": "application/json",
};

const json = (body: Record<string, unknown>, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: corsHeaders });

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (req.method === "GET") return json({ ok: true, function: "create-checkout" });
  if (req.method !== "POST") return json({ error: "Method not allowed" }, 400);

  try {
    const body = await req.json();
    const cafeName = typeof body.cafe_name === "string" ? body.cafe_name.trim() : "";
    const tier = body.tier;
    const interval = body.interval;
    if (!cafeName || !["starter", "standard", "plus"].includes(tier) || !["month", "year"].includes(interval)) {
      return json({ error: "Invalid cafe_name, tier, or interval" }, 400);
    }

    const priceEnv = {
      starter_month: "STRIPE_PRICE_STARTER",
      standard_month: "STRIPE_PRICE_STANDARD",
      plus_month: "STRIPE_PRICE_PLUS",
      starter_year: "STRIPE_PRICE_STARTER_ANNUAL",
      standard_year: "STRIPE_PRICE_STANDARD_ANNUAL",
      plus_year: "STRIPE_PRICE_PLUS_ANNUAL",
    } as Record<string, string>;
    const priceId = Deno.env.get(priceEnv[`${tier}_${interval}`]);
    const stripeKey = Deno.env.get("STRIPE_SECRET_KEY");
    if (!stripeKey || !priceId) return json({ error: "Stripe checkout is not configured" }, 400);

    const appUrl = Deno.env.get("APP_URL") ?? "https://roster-cafe.streamlit.app";
    const cancelUrl = Deno.env.get("LANDING_URL") ?? "https://escala.madfrog.ie";
    const form = new URLSearchParams();
    form.set("mode", "subscription");
    form.set("line_items[0][price]", priceId);
    form.set("line_items[0][quantity]", "1");
    form.set("subscription_data[trial_period_days]", "15");
    form.set("subscription_data[metadata][tenant_id]", "0");
    form.set("subscription_data[metadata][tier]", tier);
    form.set("subscription_data[metadata][cafe_name]", cafeName);
    form.set("metadata[tenant_id]", "0");
    form.set("metadata[tier]", tier);
    form.set("metadata[cafe_name]", cafeName);
    form.set("success_url", `${appUrl}?registered=1`);
    form.set("cancel_url", cancelUrl);

    const response = await fetch("https://api.stripe.com/v1/checkout/sessions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${stripeKey}`,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: form.toString(),
    });
    const session = await response.json();
    if (!response.ok || !session.url) {
      throw new Error(session.error?.message ?? "Stripe did not return a checkout URL");
    }
    return json({ url: session.url });
  } catch (error) {
    console.error("Create checkout failed:", error);
    return json({ error: error instanceof Error ? error.message : "Could not create checkout" }, 400);
  }
});
