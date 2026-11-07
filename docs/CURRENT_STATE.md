# Current State

> Single source of truth. Update this file at the end of every session.

---

## Active Phase

**Phase 8 — Billing & Subscription (Stripe)** *(in progress — full checkout flow tested end-to-end; webhook updating DB correctly; launch package pending)*

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
| `app.py` | Fixed DATABASE_URL missing from Streamlit Secrets (was using ephemeral SQLite); added ?upgraded=1 post-payment redirect handling with session banner |
| `billing_logic.py` | Fixed Stripe checkout price: €39.90 one-time setup + €20/month recurring; updated product names to "Roster Café" branding |
| `supabase/functions/stripe-webhook/index.ts` | Fixed table name capitalisation: "Subscriptions" → "subscriptions" (PostgreSQL normalises to lowercase); redeployed to production |

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

- **Credentials rotation (manual action required)** — Supabase DB password and admin@cafe.com password need to be rotated.
- **Budget thresholds (290/300/305h) hardcoded** — Balsbridge-specific, multi-tenancy gap, not critical yet.
- **Stripe test mode** — all keys are test keys; must switch to live keys before accepting real payments.

---

## Next Immediate Steps

**Launch Package (all to do before going live):**
1. **Register domain** — `madfrog.ie` via Blacknight or Namecheap (~€25/year); OR deploy to `roster-cafe.pages.dev` free first.
2. **Deploy landing page** — connect `nandocaetano/roster-cafe` to Cloudflare Pages, `public/` as root.
3. **Zoho Mail free** — custom domain email `@madfrog.ie`; add MX records in Cloudflare DNS.
4. **Switch Stripe to live mode** — replace `sk_test_...` keys with live keys in Streamlit Secrets and Supabase Edge Function secrets; re-register webhook with live endpoint.
5. **Credentials rotation** — rotate Supabase DB password + admin@cafe.com via Password Reset UI.

---

## Session Workflow Rules

- **STARTUP**: Read this file first before any code change.
- **WRAP-UP**: Update *Modified Files*, *Blockers*, and *Next Immediate Steps* before closing the session.
