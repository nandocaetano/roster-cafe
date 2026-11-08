/**
 * Stripe webhook handler — Supabase Edge Function
 *
 * Events handled:
 *   checkout.session.completed  → UPSERT pro subscription row
 *   customer.subscription.deleted → downgrade the tenant to free
 *
 * Required secrets (Supabase Dashboard → Project Settings → Edge Functions):
 *   STRIPE_SECRET_KEY       — Stripe secret key
 *   STRIPE_WEBHOOK_SECRET   — from Stripe Dashboard → Webhooks → signing secret
 *   SUPABASE_URL            — auto-available in Edge Functions
 *   SUPABASE_SERVICE_ROLE_KEY — auto-available in Edge Functions
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import Stripe from "stripe";
import { createClient } from "npm:@supabase/supabase-js@2";

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
    const message = err instanceof Error ? err.message : "Invalid signature";
    console.error("Signature verification failed:", message);
    return new Response(`Webhook Error: ${message}`, { status: 400 });
  }

  try {
    // ── Payment confirmed → create tenant or upgrade an existing tenant ─────
    if (event.type === "checkout.session.completed") {
      const session = event.data.object as Stripe.Checkout.Session;
      let tenantId = parseInt(session.metadata?.tenant_id ?? "0", 10) || 0;
      const customerEmail = session.customer_details?.email ?? session.customer_email ?? null;
      const cafeName = session.metadata?.cafe_name?.trim() || "New Cafe";

      if (tenantId <= 0) {
        if (!customerEmail) {
          console.error("New checkout has no customer email; account creation skipped");
        } else {
          const { data: cafe, error: cafeError } = await supabase
            .from("cafes")
            .insert({ name: cafeName, admin_email: customerEmail, created_at: new Date().toISOString() })
            .select("id")
            .single();
          if (cafeError) throw cafeError;

          tenantId = cafe.id;
          const password = crypto.randomUUID().slice(0, 12);
          const enc = new TextEncoder();
          const salt = crypto.getRandomValues(new Uint8Array(16));
          const passwordBytes = enc.encode(password);
          const hashInput = new Uint8Array(salt.length + passwordBytes.length);
          hashInput.set(salt);
          hashInput.set(passwordBytes, salt.length);
          const hashBuffer = await crypto.subtle.digest("SHA-256", hashInput);
          const toHex = (bytes: Uint8Array) => Array.from(bytes).map((b) => b.toString(16).padStart(2, "0")).join("");
          const passwordHash = `${toHex(salt)}:${toHex(new Uint8Array(hashBuffer))}`;

          const { error: userError } = await supabase.from("users").insert({
            tenant_id: tenantId,
            email: customerEmail,
            password_hash: passwordHash,
            role: "admin",
            created_at: new Date().toISOString(),
          });
          if (userError) throw userError;

          // Credentials are stored for the onboarding flow; failure here must not fail Stripe delivery.
          const { error: credentialsError } = await supabase.from("pendingcredentials").insert({
            email: customerEmail,
            temp_password: password,
            cafe_id: tenantId,
            used: false,
            created_at: new Date().toISOString(),
          });
          if (credentialsError) {
            console.error("Pending credentials storage failed:", credentialsError);
          }
          const resendKey = Deno.env.get('RESEND_API_KEY');
          if (resendKey && customerEmail && password) {
            try {
              const appUrl = Deno.env.get('APP_URL') ?? 'https://roster-cafe.streamlit.app';
              const emailHtml = '<!DOCTYPE html><html><body style="font-family:sans-serif;max-width:520px;margin:0 auto;color:#1a1a2e;padding:24px"><p style="font-size:22px;font-weight:700;margin:0 0 4px">escala</p><p style="color:#888;font-size:13px;margin:0 0 28px">Cafe rota management</p><p>Hi,</p><p>Your 15-day trial is active. Here are your login details:</p><div style="background:#f5f5f5;border-radius:8px;padding:16px;margin:20px 0"><p style="margin:0 0 8px"><strong>Email:</strong> ' + customerEmail + '</p><p style="margin:0"><strong>Temporary password:</strong> ' + password + '</p></div><p><a href="' + appUrl + '" style="background:#7c3aed;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;display:inline-block">Open escala</a></p><p style="margin-top:24px;font-size:13px;color:#888">Add your team, set your shifts, and generate your first rota in under 10 minutes.</p><hr style="border:none;border-top:1px solid #eee;margin:28px 0"><p style="font-size:12px;color:#aaa">escala by Mad Frog Studio - Dublin - hello@madfrog.ie</p></body></html>';
              await fetch('https://api.resend.com/emails', {
                method: 'POST',
                headers: {
                  'Authorization': 'Bearer ' + resendKey,
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                  from: 'escala <hello@madfrog.ie>',
                  to: [customerEmail],
                  subject: 'You are in - open your escala roster',
                  html: emailHtml,
                }),
              });
            } catch (emailErr) {
              console.error('Welcome email failed:', emailErr);
            }
          }
        }
      }

      const subscriptionId = typeof session.subscription === "string" ? session.subscription : null;
      const customerId = typeof session.customer === "string" ? session.customer : null;
      const tier = session.metadata?.tier ?? "starter";

      const { error } = await supabase.from("subscriptions").insert({
        tenant_id: tenantId,
        plano: tier,
        validade: null,
        stripe_customer_id: customerId,
        stripe_subscription_id: subscriptionId,
        criado_em: new Date().toISOString(),
      });
      if (error) throw error;
      console.log(`Tenant ${tenantId} → ${tier} (subscription active)`);
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
        return new Response(JSON.stringify({ received: true, warning: "Could not resolve tenant" }), {
          headers: { "Content-Type": "application/json" },
        });
      }

      const { error } = await supabase.from("subscriptions").insert({
        tenant_id: tenantId,
        plano: "free",
        validade: null,
        criado_em: new Date().toISOString(),
      });
      if (error) throw error;
      console.log(`Tenant ${tenantId} → free (subscription cancelled)`);
    }
  } catch (err) {
    console.error("Error processing webhook:", err);
    return new Response(JSON.stringify({ received: true, warning: "Webhook processing failed" }), {
      headers: { "Content-Type": "application/json" },
    });
  }

  return new Response(JSON.stringify({ received: true }), {
    headers: { "Content-Type": "application/json" },
  });
});
