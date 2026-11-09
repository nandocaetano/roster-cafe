> Leia também LEIA-ME.md e docs/DECISIONS.md antes de começar (padrão Mad Frog, 2026-11-09). Preço oficial: D-003.
# Current State

> Single source of truth. Update this file at the end of every session.

---

## Active Phase

**Phase 8 — Stripe Billing & Launch Prep** *(in progress)*

- ✅ UX audit completo (ux-menu-architect) — tab order, CTA primário, mensagens, Histórico separado
- ✅ Trial paywall guard (aba2 + aba3, 7 dias, _trial_expired())
- ✅ Stripe checkout corrigido: sem setup fee, trial_period_days=7 (D-008)
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
- ✅ Paywall gate implementado — tenant sem subscription vê trial wall com seletor de tier (app.py)
- ✅ Preços corrigidos na UI — Starter €19 / Standard €39 / Plus €65 (sidebar + trial walls)
- ✅ Trial wall atualizado — seletor de 3 tiers em vez de botão hardcoded para Starter
- ✅ Self-registration — stripe-webhook auto-cria Cafe+User com password temporária após checkout (tenant_id=0)
- ✅ Welcome email via Resend — webhook envia credenciais por email após criar conta
- ✅ Resend configurado — domínio madfrog.ie adicionado, DNS records no Cloudflare, RESEND_API_KEY no Supabase
- ✅ Edge Function create-checkout — nova função para landing page iniciar checkout com nome do café
- ✅ Landing page atualizada — modal com nome do café + seletor de tier + Stripe checkout real (substitui mailto:)
- ✅ Modal bug corrigido e deployado — `display:none` em vez de `hidden`, closeModal corrigido (Cloudflare Workers v9b769bd4)
- ✅ `create-checkout` re-deployada com `--no-verify-jwt` (antes exigia JWT, landing pública não autenticada)
- ✅ `payment_method_types` removido do `create-checkout` (parâmetro descontinuado pelo Stripe)
- ✅ `STRIPE_SECRET_KEY` no Supabase corrigido (estava salvo com aspas, agora sem)
- ✅ Checkout end-to-end funcionando — modal → Stripe Checkout abre corretamente
- ✅ `.claude/settings.local.json` — permissões `npx wrangler *` e `npm run *` adicionadas (local, não commitado)
- ✅ SaaS Bootstrap Kit criado — Artifact com prompt mestre + estrutura completa do ambiente Maestri para reusar em novos projetos
- ✅ Dias de folga mínimos por semana — coluna `min_dias_folga` em `Cafes`, constraint CP-SAT no solver, UI na Aba 5 (admin/superadmin)
- ✅ **[CRÍTICO RESOLVIDO] STRIPE_WEBHOOK_SECRET corrigido** — secret estava errado no Supabase; atualizado via CLI + redeploy da stripe-webhook Edge Function
- ✅ **Teste end-to-end completo** — landing → create-checkout → Stripe Checkout → webhook → Cafe+User+Subscription+pendingcredentials criados → login com password temporária → app abre no plano correto (Starter, staff limit 10)
- ⏳ **[PRÉ-LAUNCH] Resend DNS** — verificação do domínio madfrog.ie ainda a propagar no Cloudflare (email de welcome não entrega até DNS verde)
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

## Modified Files (last session — 2026-11-09)

| File | Last Change |
|---|---|
| `docs/CURRENT_STATE.md` | Trial 7 dias confirmado via Playwright E2E; push main confirmado |
| `docs/DECISIONS.md` | D-006, D-007, D-008 registados |
| `docs/AGENTS.md` | Regra smoke test antes de push em main |
| `billing_logic.py` | trial_period_days 15→7 |
| `app.py` | Mensagens "15-day" → "7-day" |
| `supabase/functions/create-checkout/index.ts` | trial_period_days "15"→"7" |
| `supabase/functions/stripe-webhook/index.ts` | Email template "15-day"→"7-day" |
| `tests/test_smoke.py` | Novo — smoke test de imports |
| `tests/evidence/` | Screenshots Playwright E2E (gitignored) |

> **Infra alterada (fora do git):** `create-checkout` e `stripe-webhook` Edge Functions redeployadas (trial=7 dias, --no-verify-jwt). Push `42531f5..22d158c` → `origin/main` concluído em 2026-11-09.

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

- **[BLOQUEADOR EXTERNO] madfrog.ie NXDOMAIN** — retenção de registo no Register365, aguarda documento IEDR. Sem ação técnica possível. Resend DNS e landing pública ficam bloqueados até liberar.
- **[RLS desligado]** — `cafes`, `users`, `funcionarios`, `rosters`, `subscriptions` sem Row Level Security. Políticas propostas (ver SQL abaixo em § RLS Proposal). Aplicar antes de go-live (HITL).
- **Credentials rotation (HITL)** — Supabase DB password + admin email precisam de rotação antes do go-live.
- **Budget thresholds (290/300/305h) hardcoded** — Balsbridge-specific, multi-tenancy gap, not critical yet.
- **Stripe test mode** — all keys are test keys; must switch to live keys before accepting real payments (HITL).

---

## Next Immediate Steps

1. **Aguardar madfrog.ie** — bloqueador externo (Register365/IEDR). Quando domínio liberar: deploy landing + verificar Resend DNS + testar welcome email.
2. **Aplicar RLS** — aprovar e aplicar políticas propostas no Supabase (ver § RLS Proposal). Teste em staging antes. Entra no checklist D-007 antes do go-live.
3. **Switch Stripe para live mode** — substituir sk_test por live keys (HITL, requer aprovação explícita)
4. **Credentials rotation** — Supabase DB password + admin email (HITL, requer aprovação)

---

## Session Workflow Rules

- **STARTUP**: Read this file first before any code change.
- **WRAP-UP**: Update *Modified Files*, *Blockers*, and *Next Immediate Steps* before closing the session.
