/**
 * Stripe webhook handler — Supabase Edge Function
 *
 * Events handled:
 *   checkout.session.completed  → INSERT pro subscription row
 *   customer.subscription.deleted → INSERT free row (downgrade)
 *
 * Required secrets (Supabase Dashboard → Project Settings → Edge Functions):
 *   STRIPE_SECRET_KEY       — Stripe secret key
 *   STRIPE_WEBHOOK_SECRET   — from Stripe Dashboard → Webhooks → signing secret
 *   SUPABASE_URL            — auto-available in Edge Functions
 *   SUPABASE_SERVICE_ROLE_KEY — auto-available in Edge Functions
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import Stripe from "https://esm.sh/stripe@12.18.0?target=deno&no-check";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.38.0";

const stripe = new Stripe(Deno.env.get("STRIPE_SECRET_KEY") ?? "", {
  apiVersion: "2023-10-16",
  httpClient: Stripe.createFetchHttpClient(),
});

const supabase = createClient(
  Deno.env.get("SUPABASE_URL") ?? "",
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "",
);

serve(async (req: Request) => {
  const body = await req.text();
  const sig = req.headers.get("stripe-signature") ?? "";
  const webhookSecret = Deno.env.get("STRIPE_WEBHOOK_SECRET") ?? "";

  let event: Stripe.Event;
  try {
    event = await stripe.webhooks.constructEventAsync(body, sig, webhookSecret);
  } catch (err) {
    console.error("Signature verification failed:", err.message);
    return new Response(`Webhook Error: ${err.message}`, { status: 400 });
  }

  try {
    // ── Payment confirmed → upgrade to Pro ──────────────────────────────────
    if (event.type === "checkout.session.completed") {
      const session = event.data.object as Stripe.Checkout.Session;
      const tenantId = parseInt(session.metadata?.tenant_id ?? "0", 10);
      if (!tenantId) {
        return new Response("Missing tenant_id in session metadata", { status: 400 });
      }

      const subscriptionId = session.subscription as string;
      const sub = await stripe.subscriptions.retrieve(subscriptionId);
      const validade = new Date(sub.current_period_end * 1000).toISOString();

      const { error } = await supabase.from("subscriptions").insert({
        tenant_id: tenantId,
        plano: "pro",
        validade,
        stripe_subscription_id: subscriptionId,
        criado_em: new Date().toISOString(),
      });
      if (error) throw error;
      console.log(`Tenant ${tenantId} → Pro, valid until ${validade}`);
    }

    // ── Subscription cancelled → downgrade to Free ──────────────────────────
    if (event.type === "customer.subscription.deleted") {
      const sub = event.data.object as Stripe.Subscription;

      // tenant_id in subscription metadata (set via subscription_data in billing_logic.py)
      let tenantId = parseInt(sub.metadata?.tenant_id ?? "0", 10);

      // Fallback: look up by stripe_subscription_id stored in Subscriptions table
      if (!tenantId) {
        const { data } = await supabase
          .from("subscriptions")
          .select("tenant_id")
          .eq("stripe_subscription_id", sub.id)
          .order("criado_em", { ascending: false })
          .limit(1)
          .single();
        tenantId = data?.tenant_id ?? 0;
      }

      if (!tenantId) {
        console.error(`Could not resolve tenant_id for subscription ${sub.id}`);
        return new Response("Could not resolve tenant", { status: 400 });
      }

      const { error } = await supabase.from("subscriptions").insert({
        tenant_id: tenantId,
        plano: "free",
        criado_em: new Date().toISOString(),
      });
      if (error) throw error;
      console.log(`Tenant ${tenantId} → Free (subscription cancelled)`);
    }
  } catch (err) {
    console.error("Error processing webhook:", err);
    return new Response("Internal server error", { status: 500 });
  }

  return new Response(JSON.stringify({ received: true }), {
    headers: { "Content-Type": "application/json" },
  });
});
