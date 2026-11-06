# Current State

> Single source of truth. Update this file at the end of every session.

---

## Active Phase

**Phase 8 — Billing & Subscription (Stripe)** *(in progress — billing gates + webhook built; Stripe test mode configured under Mad Frog; deploy + secrets pending)*

**Add-ons A+B — Fairness Score + Preference Weighting** *(complete — merged into solver)*

---

## Completed Phases

| Phase | Description | Status |
|---|---|---|
| 1 | Modularisation — split monolithic app.py into app.py / database.py / logic.py | ✅ Complete |
| 2 | Multi-Tenancy — Cafes table, tenant_id FK on Funcionarios, all CRUD scoped by tenant | ✅ Complete |
| 3 | Authentication — Users table, SHA-256 + salt hashing, Login/Register UI, session auth gate, sidebar with logout | ✅ Complete |
| 4 | Algorithm & WTI Constraints — clopening, keyholder, 11h rest, break warnings | ✅ Complete |
| 5 | Weekly Overrides + Export + Analytics — Folga/Férias/Treinamento, margem, CSV/Excel/PDF, Roster History, Tab 4 | ✅ Complete |
| 6 | RBAC & Commercial Limits — superadmin, registro bloqueado, limite 20 funcionários, login UI card, Aba 5 Ajuda | ✅ Complete |
| 7 | Persistent Database (Supabase/PostgreSQL) — psycopg2 dual-backend, DATABASE_URL secret, live on Streamlit Cloud | ✅ Complete |

---

## Modified Files (last session)

| File | Last Change |
|---|---|
| `scratchpad/landing.html` | Impeccable polish v6: keyholder role data corrected (Barista→Asst.Manager/Head Barista), CTA consistency (all "Start 7-day trial"), light-mode neutral chroma fix, browser surface tokens, word count 455→446, sloplint 0 FAIL 2 REFLEX(waived). Artifact: https://claude.ai/artifact/Me2iNCAfc8K4oSuHG1DvZJ |

---

## Current Architecture Snapshot

```
app_escala/
├── app.py          # Streamlit UI — 5 tabs + auth gate + sidebar + @st.cache_data wrappers
├── database.py     # Dual-backend CRUD (psycopg2 when DATABASE_URL set, sqlite3 otherwise)
├── logic.py        # Pure Python — shift math, availability, urgency scheduler, PDF export
├── requirements.txt
└── docs/           # This Second Brain
```

**DB in production:** PostgreSQL via Supabase (Transaction pooler, Frankfurt).  
**DB in local dev:** SQLite (`roster_cafe.db`, created at runtime, not committed).

---

## Blockers

- **`STRIPE_SECRET_KEY` not configured** — add to Streamlit Cloud Secrets before checkout works. UI shows a friendly warning when missing.
- **`APP_URL` not configured** — add `APP_URL = https://your-actual-app.streamlit.app` to Streamlit Cloud Secrets for Stripe success/cancel redirect URLs.
- **Supabase `Subscriptions` table** — `init_db()` creates it via `CREATE TABLE IF NOT EXISTS`, so it will auto-create on next cold start in Supabase. No manual SQL needed.
- **Credentials rotation (manual action required)** — Supabase DB password and admin@cafe.com password need to be rotated.
- **Budget thresholds (290/300/305h) hardcoded** — Balsbridge-specific, multi-tenancy gap, not critical yet.

---

## Next Immediate Steps

1. **Copy landing page to stable path** — move/rename `scratchpad/landing.html` to repo root or `public/index.html` for hosting on madfrog.ie or Streamlit Cloud.
2. **Deploy Edge Function** — `supabase functions deploy stripe-webhook` (requires Supabase CLI + `supabase link`).
3. **Deploy Edge Function** — `supabase functions deploy stripe-webhook` (requires Supabase CLI + `supabase link`).
4. **Add Stripe secrets** — Streamlit Cloud: `STRIPE_SECRET_KEY` + `APP_URL`. Supabase Edge Functions: `STRIPE_WEBHOOK_SECRET` + `STRIPE_SECRET_KEY`.
5. **Register webhook in Stripe** — Dashboard → Developers → Webhooks → `https://nbggytkbrxqhnqvtvbpl.supabase.co/functions/v1/stripe-webhook`. Events: `checkout.session.completed`, `customer.subscription.deleted`.
6. **License key flow** — implement `LicenseKeys` table + activation step in registration flow.
7. **Credentials rotation (manual)** — rotate Supabase DB password + admin@cafe.com via Password Reset UI.
8. **billing_logic.py** — replace free/pro model with trial/paid (`plano = 'trial'` with `validade`).

---

## Session Workflow Rules

- **STARTUP**: Read this file first before any code change.
- **WRAP-UP**: Update *Modified Files*, *Blockers*, and *Next Immediate Steps* before closing the session.
