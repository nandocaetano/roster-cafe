# Current State

> Single source of truth. Update this file at the end of every session.

---

## Active Phase

**Phase 8 — Billing & Subscription (Stripe)** *(in progress — billing gates wired into app.py; Stripe key + webhook pending)*

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
| `app.py` | Phase 8 billing wiring: `import os` + billing_logic imports; `_is_pro`/`_emp_limit` computed at runtime; sidebar Upgrade to Pro panel (non-superadmin); Tab 1 dynamic employee cap; Tab 3 PDF export gated; Tab 3 Roster History gated; Tab 4 Analytics gated |
| `billing_logic.py` | Added `except Exception: return {"plano": "free"}` to `get_subscription()` — graceful fallback when Subscriptions table missing |
| `database.py` | Added `Subscriptions` table schema to both PG and SQLite `init_db()` blocks; seed free-plan row for tenant_id=1 |

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

1. **Add Streamlit Cloud Secrets** — `STRIPE_SECRET_KEY` (from Stripe dashboard) + `APP_URL` (live app URL). Checkout button will then work end-to-end.
2. **Stripe webhook** — POST `/webhook` endpoint to update `Subscriptions.plano` on `checkout.session.completed` and `customer.subscription.deleted` events.
3. **Supabase manual migration (if needed)** — run `ALTER TABLE Funcionarios ADD COLUMN IF NOT EXISTS preferencia_turno TEXT DEFAULT 'Sem preferência'` in Supabase SQL Editor to sync the preference column if Supabase was not restarted.
4. **Landing page** — run `/rea-analyze` on Deputy/7shifts first, then build from `docs/GTM_STRATEGY.md` copy.
5. **Credentials rotation (manual)** — rotate Supabase DB password + admin@cafe.com via Password Reset UI.

---

## Session Workflow Rules

- **STARTUP**: Read this file first before any code change.
- **WRAP-UP**: Update *Modified Files*, *Blockers*, and *Next Immediate Steps* before closing the session.
