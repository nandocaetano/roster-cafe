# Current State

> Single source of truth. Update this file at the end of every session.

---

## Active Phase

**Phase 8 — Stripe Billing & Launch Prep** *(in progress)*

- ✅ UX audit completo (ux-menu-architect) — tab order, CTA primário, mensagens, Histórico separado
- ✅ Trial paywall guard (aba2 + aba3, 15 dias, _trial_expired())
- ✅ Stripe checkout corrigido: sem setup fee, trial_period_days=15
- ✅ upsert_subscription() helper adicionado a billing_logic.py
- ✅ Webhook Supabase Edge Function deployed (`stripe-webhook` → projeto `nbggytkbrxqhnqvtvbpl`)
- ✅ `escala-landing` git init + commit limpo (12 source files, node_modules/dist/.astro excluídos via .gitignore)
- ✅ Webhook registado no Stripe Dashboard (`escala-supabase-webhook`, 2 eventos, URL Supabase)
- ⏳ Copiar `STRIPE_WEBHOOK_SECRET` (whsec_...) do Stripe Dashboard → Supabase Edge Function secrets
- ✅ GitHub repo `escala-landing` criado e push feito (github.com/nandocaetano/escala-landing, branch: main)
- ✅ Landing page deployed (escala-landing.caetanolasko.workers.dev + escala.madfrog.ie configurado)
- ⏳ Switch Stripe para live mode (requer aprovação explícita — HITL)

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
| 9 | Persistent Shift Configuration — ShiftTemplates, WeeklySetup, editable shifts/headcount, tenant-scoped persistence | ✅ Complete |

---

## Modified Files (last session)

| File | Last Change |
|---|---|
| `app.py` | Full PT→EN translation — login, tabs, sidebar, all 6 tabs, help tab |

---

## Current Architecture Snapshot

```
app_escala/
├── app.py          # Streamlit UI — 6 tabs + auth gate + sidebar + @st.cache_data wrappers
├── database.py     # Dual-backend CRUD plus tenant-scoped configuration persistence
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

1. **git push** — push PT→EN translation to remote + deploy to Streamlit Cloud
2. **Test billing flow** — Stripe test mode checkout → verify Pro activates in DB
3. **Switch Stripe to live mode** — replace `sk_test_...` with live keys (HITL, requires explicit approval)
4. **Credentials rotation** — Supabase DB password + admin@cafe.com (HITL, requires approval)
5. ✅ **GitHub** — repo `escala-landing` pushed (github.com/nandocaetano/escala-landing)
6. ✅ **Cloudflare Workers** — deployed `escala.madfrog.ie`
7. ✅ **Stripe webhook** — `escala-supabase-webhook` active, secrets configured in Supabase

---

## Session Workflow Rules

- **STARTUP**: Read this file first before any code change.
- **WRAP-UP**: Update *Modified Files*, *Blockers*, and *Next Immediate Steps* before closing the session.
