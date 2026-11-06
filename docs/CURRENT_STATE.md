# Current State

> Single source of truth. Update this file at the end of every session.

---

## Active Phase

**Phase 8 — Billing & Subscription (Stripe)** *(not yet started)*

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
| `billing_logic.py` | New file (CODEX) — get_subscription, is_pro, get_employee_limit, check_feature_gate, create_stripe_checkout_session for Phase 8 billing |
| `requirements.txt` | Added `stripe>=7.0.0` |
| `docs/GTM_STRATEGY.md` | New file (GROK) — full Dublin GTM: acquisition channels, landing copy, cold email script, WTI sales argument, month-1 metrics, 14-day playbook |
| **Supabase DB** | `Subscriptions` table created + seed row tenant_id=1 plano='free' |

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

- **Stripe secret key not configured** — `STRIPE_SECRET_KEY` needs to be added to Streamlit Cloud Secrets before `create_stripe_checkout_session()` works in production.
- **Credentials rotation (manual action required)** — Supabase DB password and admin@cafe.com password need to be rotated by the user in the Supabase dashboard + Streamlit Cloud Secrets.
- **Budget thresholds (290/300/305h) hardcoded** — these are Balsbridge-specific numbers global to all tenants. Multi-tenancy design gap, not critical yet.

---

## Next Immediate Steps

1. **Wire billing_logic.py into app.py** — import check_feature_gate + get_employee_limit; gate PDF export (Tab 3), Analytics (Tab 4), Roster History (Tab 3) behind feature check; replace hardcoded EMPLOYEE_LIMIT with get_employee_limit().
2. **Stripe Checkout UI** — add "Upgrade to Pro" button in sidebar for non-superadmin users, calling create_stripe_checkout_session(); add STRIPE_SECRET_KEY to Streamlit Cloud Secrets.
3. **Stripe webhook** — POST /webhook endpoint to update Subscriptions.plano on paid/cancelled events.
4. **Landing page** — use docs/GTM_STRATEGY.md copy to build public landing page.
5. **Credentials rotation (manual):** rotate Supabase DB password + admin@cafe.com via Password Reset UI.

---

## Session Workflow Rules

- **STARTUP**: Read this file first before any code change.
- **WRAP-UP**: Update *Modified Files*, *Blockers*, and *Next Immediate Steps* before closing the session.
