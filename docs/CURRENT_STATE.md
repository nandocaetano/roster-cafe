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
| `docs/ARCHITECTURE.md` | Remove setup fee €39.90 stale |
| `docs/CURRENT_STATE.md` | Actualizado com progresso Phase 8 |
| `escala-landing/.gitignore` | Novo — exclui node_modules/, dist/, .env |
| `escala-landing/wrangler.toml` | Novo — Cloudflare Workers assets config |
| `escala-landing/` (git repo) | git init + commit limpo, push para GitHub, deployed Cloudflare Workers |

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

1. **Supabase Dashboard** → Edge Functions → stripe-webhook → Environment variables:
   - `STRIPE_WEBHOOK_SECRET` — copiar o `whsec_...` do Stripe Dashboard (Developers → Webhooks → escala-supabase-webhook → Segredo da assinatura → clica no olho para revelar)
   - `STRIPE_SECRET_KEY` — a chave `sk_test_...` já usada no Streamlit Secrets
2. **Testar flow completo** em test mode — fazer checkout, verificar subscrição Pro activa na DB
3. ✅ **GitHub** — repo `escala-landing` criado e push feito (github.com/nandocaetano/escala-landing)
4. ✅ **Cloudflare Workers** — deployed `escala-landing.caetanolasko.workers.dev`, domínio `escala.madfrog.ie` configurado (DNS a propagar)
5. **Switch Stripe para live mode** — substituir `sk_test_...` por live keys (requer aprovação explícita — HITL)
6. **Credentials rotation** — rodar password Supabase DB + admin@cafe.com (requer aprovação)

---

## Session Workflow Rules

- **STARTUP**: Read this file first before any code change.
- **WRAP-UP**: Update *Modified Files*, *Blockers*, and *Next Immediate Steps* before closing the session.
