# Current State

> Single source of truth. Update this file at the end of every session.

---

## Active Phase

**Phase 8 — Stripe Billing & Launch Prep** *(in progress)*

- ✅ UX audit completo (ux-menu-architect) — tab order, CTA primário, mensagens, Histórico separado
- ✅ Trial paywall guard (aba2 + aba3, 15 dias, _trial_expired())
- ✅ Stripe checkout corrigido: sem setup fee, trial_period_days=15
- ✅ 4 tiers de preços: Starter/Standard/Plus/Network — billing_logic.py refatorado
- ✅ billing_logic.py: TIER_LIMITS, TIER_PRICES_CENTS, TIER_PRICES_ANNUAL_CENTS, create_stripe_checkout_session com interval='month'|'year'
- ✅ database.py: EMPLOYEE_LIMIT elevado para 100 (cap de segurança; Plus exige >20)
- ✅ Edge Function stripe-webhook: INSERT audit trail, tier lido de session.metadata, sem UPSERT
- ✅ Webhook Supabase Edge Function deployed (`stripe-webhook` → projeto `nbggytkbrxqhnqvtvbpl`)
- ✅ `escala-landing` git init + commit limpo (12 source files, node_modules/dist/.astro excluídos via .gitignore)
- ✅ Webhook registado no Stripe Dashboard (`escala-supabase-webhook`, 2 eventos, URL Supabase)
- ✅ Supabase Edge Function secrets: STRIPE_SECRET_KEY + STRIPE_WEBHOOK_SECRET confirmados
- ✅ Produtos Stripe criados: Starter/Standard/Pro com preços mensais e anuais (6 price IDs)
- ✅ Streamlit Cloud secrets: 6 price IDs + APP_URL adicionados
- ✅ GitHub repo `escala-landing` criado e push feito (github.com/nandocaetano/escala-landing, branch: main)
- ✅ Landing page deployed (escala-landing.caetanolasko.workers.dev + escala.madfrog.ie configurado)
- ✅ Hero headline aprovado: "Your roster done in minutes!" + subtítulo Irish law
- ✅ Pricing page: 4 cards com toggle Mensal/Anual, 2 meses grátis messaging
- ✅ Re-deploy Edge Function — deployed e confirmado
- ✅ Adicionar STRIPE_SECRET_KEY ao Streamlit Cloud secrets — confirmado
- ✅ Login redesign — ⬡ hex mark, Outfit 700, dark card, tagline Dublin
- ✅ StreamlitMixedNumericTypesError corrigido (training hours input, app.py:674)
- ✅ Prod DB tables criadas manualmente no SQL Editor (shifttemplates, weeklysetup, dateheadcountoverrides — lowercase)
- ✅ Admin user reset com credenciais novas
- ⏳ **[CRÍTICO-1] Paywall gate** — tenant sem subscription Stripe acessa app 15 dias grátis sem cartão; implementar paywall na primeira entrada
- ⏳ **[CRÍTICO-2] Preços errados na UI** — sidebar mostra Starter €20/Standard €35/Plus €55; corretos são €19/€39/€65
- ⏳ **[CRÍTICO-3] Trial wall hardcoded** — botão Upgrade Now vai direto ao Starter sem escolha de tier
- ⏳ **[GTM-BLOCKER] Self-registration** — após pagar no Stripe, cliente não consegue criar conta; toda conta é criada pelo superadmin
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
| `billing_logic.py` | 4-tier pricing + annual billing + TIER_LIMITS/PRICES/ENV dicts + audit trail INSERT |
| `database.py` | EMPLOYEE_LIMIT elevado de 20 para 100 (cap de segurança para Plus/Network) |
| `supabase/functions/stripe-webhook/index.ts` | INSERT audit trail, tier de session.metadata, sem UPSERT |
| `skills/saas-headline-copywriter.md` | Nova skill — 3 fórmulas de headline para SaaS B2B |
| `skills/awesome-prompts-advertiser.md` | Nova skill — framework de copy para hero sections |
| `skills/pricing_strategy.md` | Skill reconstruída — GTM analyst, unit economics, tier logic |

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

- **[PRÉ-LAUNCH] Paywall gate ausente** — tenant sem Stripe subscription acessa app grátis sem cartão (viola modelo acordado).
- **[PRÉ-LAUNCH] Self-registration ausente** — cliente que paga no Stripe não consegue criar conta sozinho; superadmin faz manualmente.
- **[PRÉ-LAUNCH] Preços errados na UI** — sidebar e trial wall mostram valores incorretos.
- **Credentials rotation (manual action required)** — Supabase DB password and admin email password need to be rotated.
- **Budget thresholds (290/300/305h) hardcoded** — Balsbridge-specific, multi-tenancy gap, not critical yet.
- **Stripe test mode** — all keys are test keys; must switch to live keys before accepting real payments.

---

## Next Immediate Steps

1. **[Codex] Fix app.py — paywall gate + preços corretos + trial wall com seletor de tier** (em progresso)
2. **[Codex] Self-registration flow** — webhook Edge Function auto-cria Cafe+User após checkout.session.completed
3. **Testar billing flow** — Stripe test mode checkout → verificar tier na DB
4. **Switch Stripe para live mode** — substituir sk_test por live keys (HITL, requer aprovação explícita)
5. **Credentials rotation** — Supabase DB password + admin email (HITL, requer aprovação)
6. **Network tier** — criar produtos Stripe para Network quando multi-loc for lançado

---

## Session Workflow Rules

- **STARTUP**: Read this file first before any code change.
- **WRAP-UP**: Update *Modified Files*, *Blockers*, and *Next Immediate Steps* before closing the session.
