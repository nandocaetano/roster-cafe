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
| `database.py` | Added `get_all_users()` (all users joined with cafe name) and `reset_password(email, new_password)` — superadmin password reset backend |
| `app.py` | Added `get_all_users` + `reset_password` imports; added "🔑 Reset de Password" expander in superadmin sidebar with user selectbox, new password + confirm inputs, 6-char minimum validation |
| `docs/ARCHITECTURE.md` | Full rewrite — dual-backend strategy, all 4 DB tables with schema, CP-SAT solver diagram, password reset flow, updated session state keys table, deployment section |
| `docs/ROADMAP.md` | Phase 8 scope clarified: Stripe Checkout + Subscriptions table + feature gating; out-of-scope items (License Keys, Stock/Clock-in add-ons) explicitly noted |
| `.env.example` | New file — documents `DATABASE_URL` env var for local dev |

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

- **Credentials rotation (manual action required)** — Supabase DB password and admin@cafe.com password need to be rotated by the user in the Supabase dashboard + Streamlit Cloud Secrets. Code is ready (.env.example + Password Reset UI), but rotation itself is a manual step.
- **Budget thresholds (290/300/305h) hardcoded** — these are Balsbridge-specific numbers global to all tenants. Multi-tenancy design gap, not critical yet.

---

## Next Immediate Steps

1. **Phase 8 — Stripe Billing:** Add `Subscriptions` table → Stripe Checkout (20/mes) → feature gating (PDF/Analytics/history) → Stripe webhook.
2. **GTM prompt for GROK (CMO):** Pricing confirmed 39.90 setup + 20/mes. Dispatch GTM strategy + landing page copy + Dublin outreach brief. WTI compliance as main differentiator.
3. **Credentials rotation (manual):** User to rotate Supabase DB password in dashboard and update Streamlit Cloud Secrets; then use Password Reset UI (now live) to change admin@cafe.com password.

---

## Session Workflow Rules

- **STARTUP**: Read this file first before any code change.
- **WRAP-UP**: Update *Modified Files*, *Blockers*, and *Next Immediate Steps* before closing the session.
