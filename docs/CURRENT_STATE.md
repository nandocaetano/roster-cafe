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
| `logic.py` | OR-Tools CP-SAT solver replaces greedy scheduler; boolean var matrix x[e,d,s]; hard constraints (coverage, availability, 1-shift/day, max hours, keyholder, clopening 11h, novato); BIG_PENALTY objective; WTI break warnings summarised (2 lines total instead of 30+); floating point tolerance fixed (0.05h instead of 1e-9) |
| `app.py` | Duplicate `07:00–14:00` Qua slot removed (replaced with `08:00–16:00`); CP-SAT solver status shown as `st.info()` banner outside warnings expander; warnings re-categorised (erros / avisos / infos); unused `import json` removed |
| `requirements.txt` | Added `ortools>=9.8.0` |

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

- **No password reset flow** — forgotten passwords must be manually reset via Supabase SQL Editor. No self-service or admin UI exists yet.
- **Budget thresholds (290/300/305h) hardcoded** — these are Balsbridge-specific numbers global to all tenants. Multi-tenancy design gap, not critical yet.
- **Credentials rotation pending** — Supabase DB password and admin@cafe.com password should be rotated (noted previous session, still pending).

---

## Next Immediate Steps

1. **Phase 8 — Stripe Billing:** Integrate Stripe Checkout for monthly plans; add `Subscriptions` table (tenant_id, plano, validade, stripe_customer_id); gate PDF/Analytics/history behind paid plan.
2. **Add password reset UI** — superadmin can set a new password for any user in the same tenant; needed for the Natalie / Balsbridge credential situation.
3. **Update `docs/ARCHITECTURE.md`** — add Rosters table schema, `nivel` column, dual-backend section, 5-tab module map, new session state keys, caching strategy, CP-SAT solver overview.

---

## Session Workflow Rules

- **STARTUP**: Read this file first before any code change.
- **WRAP-UP**: Update *Modified Files*, *Blockers*, and *Next Immediate Steps* before closing the session.
