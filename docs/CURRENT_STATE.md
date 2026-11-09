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
- ⏳ **[PRÉ-LAUNCH] Resend DNS** — verificação do domínio madfrog.ie ainda a propagar no Cloudflare
- ⏳ **[PRÉ-LAUNCH] Teste end-to-end** — fluxo completo: landing → Stripe → webhook → email → login → primeira escala
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
| `app.py` | Leitura de `min_dias_folga` antes de gerar escala; UI de configuração na Aba 5 (admin/superadmin) |
| `database.py` | Coluna `min_dias_folga` em `Cafes` (default 1, migration idempotente); `get/set_cafe_min_dias_folga()` |
| `logic.py` | Novo parâmetro `min_dias_folga` em `gerar_escala_automatica`; constraint CP-SAT de descanso mínimo; warning WTI dinâmico |

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

- **[PRÉ-LAUNCH] Resend DNS a propagar** — domínio madfrog.ie ainda em verificação; email funciona quando verificado (nameservers Reg365 → Cloudflare pendentes).
- **Credentials rotation (manual action required)** — Supabase DB password and admin email password need to be rotated.
- **Budget thresholds (290/300/305h) hardcoded** — Balsbridge-specific, multi-tenancy gap, not critical yet.
- **Stripe test mode** — all keys are test keys; must switch to live keys before accepting real payments.

---

## Next Immediate Steps

1. **Teste end-to-end com Nati** — escala.madfrog.ie → nome do café → Stripe test card `4242 4242 4242 4242` → credenciais (via Supabase se email ainda não chegar) → login → primeira escala
2. **Confirmar Resend DNS** — verificar em resend.com/domains que madfrog.ie ficou verde (aguardando propagação dos NS Reg365 → Cloudflare)
4. **Switch Stripe para live mode** — substituir sk_test por live keys (HITL, requer aprovação explícita)
5. **Credentials rotation** — Supabase DB password + admin email (HITL, requer aprovação)

---

## Session Workflow Rules

- **STARTUP**: Read this file first before any code change.
- **WRAP-UP**: Update *Modified Files*, *Blockers*, and *Next Immediate Steps* before closing the session.
