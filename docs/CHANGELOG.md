# Changelog

---

## 2026-11-08 — Phase 8: 4-Tier Pricing, Annual Billing & Stripe Setup

### Added
- `skills/saas-headline-copywriter.md`: skill de copywriting com 3 fórmulas de headline B2B SaaS
- `skills/awesome-prompts-advertiser.md`: skill de framework para hero sections com foco no mercado irlandês
- `skills/pricing_strategy.md`: skill reconstruída — GTM analyst com unit economics e tier logic check

### Changed
- `billing_logic.py`: refatorado para 4 tiers (Starter/Standard/Plus/Network), preços mensais e anuais, `create_stripe_checkout_session` com `interval='month'|'year'`, INSERT audit trail
- `database.py`: `EMPLOYEE_LIMIT` elevado de 20 para 100 (cap de segurança; Plus exige >20 funcionários)
- `supabase/functions/stripe-webhook/index.ts`: INSERT audit trail em vez de UPSERT, tier lido de `session.metadata`, fallback por `stripe_subscription_id`
- `escala-landing/src/pages/index.astro`: headline "Your roster done in minutes!", 4 pricing cards com toggle Mensal/Anual, messaging "2 months free"

### Fixed
- `billing_logic.py`: `upsert_subscription()` → plain INSERT (não havia UNIQUE constraint em tenant_id)
- `billing_logic.py`: `EMPLOYEE_LIMIT=20` bloqueava Plus (40) e Network (ilimitado)
- `billing_logic.py`: tier ausente do metadata Stripe → Edge Function não sabia qual tier registar

### Infrastructure
- 6 produtos Stripe criados (Starter/Standard/Pro × Mensal+Anual), price IDs coletados
- Streamlit Cloud secrets: 6 price IDs + APP_URL adicionados
- Supabase Edge Function secrets: STRIPE_SECRET_KEY + STRIPE_WEBHOOK_SECRET confirmados presentes

### Files Modified
- `billing_logic.py`
- `database.py`
- `supabase/functions/stripe-webhook/index.ts`
- `skills/saas-headline-copywriter.md` (novo)
- `skills/awesome-prompts-advertiser.md` (novo)
- `skills/pricing_strategy.md` (reconstruído)
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`

---

## 2026-11-08 — Phase 8: Full PT→EN UI translation

### Changed
- `app.py`: Complete translation of all visible Portuguese copy to English
  - Login: "Gerenciador de Escalas" → "escala", "Entrar" → "Sign in", etc.
  - Tabs: "Setup da Semana/Rota da Semana/Equipa/Turnos/Histórico/Ajuda" → EN
  - Sidebar: plan info, upgrade flow, register/reset forms
  - Team tab: all labels, buttons, help text, error messages
  - Shifts tab: column headers, save/error messages (column keys changed to EN)
  - Weekly Setup tab: form fields, budget status, headcount overrides, trial paywall + inline upgrade button
  - Weekly Rota tab: buttons, warnings, roster save, trial paywall + inline upgrade button
  - History & Analytics tab: metrics, chart labels, feature gate messages
  - Help tab: full EN rewrite
  - Availability selector: English labels via `format_func`, data values unchanged (DB integrity)
  - Level/Preference selectboxes: English display labels via `format_func`, PT data values preserved

### Files Modified
- `app.py`
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`

---

## 2026-11-08 — Phase 8: Landing page deployed + Stripe webhook registered

### Added
- `escala-landing` git repo inicializado e pushed para github.com/nandocaetano/escala-landing
- `wrangler.toml` para Cloudflare Workers + Assets deploy
- Landing page deployed em `escala-landing.caetanolasko.workers.dev`
- Domínio custom `escala.madfrog.ie` configurado no Cloudflare Workers
- Webhook `escala-supabase-webhook` registado no Stripe (test mode), 2 eventos: `checkout.session.completed` + `customer.subscription.deleted`

### Fixed
- `docs/ARCHITECTURE.md`: setup fee €39.90 removido (stale desde sessão anterior)
- `escala-landing/.gitignore`: node_modules/ e dist/ excluídos do repo

### Files Modified
- `escala-landing/.gitignore` (novo)
- `escala-landing/wrangler.toml` (novo)
- `docs/ARCHITECTURE.md`
- `docs/CURRENT_STATE.md`

---

## 2026-11-07 — Phase 8: Webhook deployed + permissions config

### Added
- Supabase Edge Function `stripe-webhook` deployed para produção (projeto `nbggytkbrxqhnqvtvbpl`)
- Permissões globais no Claude Code (`~/.claude/settings.json`) para `supabase functions deploy/logs *` sem prompt
- `autoMode.allow` rules para o mesmo conjunto de comandos

### Changed
- `docs/CURRENT_STATE.md` — Next Steps actualizados com instruções detalhadas pós-deploy

### Pending (manual — requer acção do utilizador)
- Registar endpoint no Stripe Dashboard + copiar `STRIPE_WEBHOOK_SECRET`
- Adicionar secrets à Edge Function no Supabase Dashboard
- Criar repo GitHub `escala-landing` + push + Cloudflare Pages
- Switch Stripe live mode (HITL)

### Files Modified
- `docs/CURRENT_STATE.md`

---

## 2026-11-07 — Phase 9 complete: Date-specific headcount overrides

### Added
- `DateHeadcountOverrides` table in both PostgreSQL and SQLite branches of `init_db()`, with `UNIQUE (tenant_id, override_date, shift_label)` constraint.
- Three CRUD functions in `database.py`: `get_date_headcount_overrides`, `save_date_headcount_override`, `delete_date_headcount_override`, following the existing dual-backend pattern.
- "📅 Exceções de headcount por data" expander in aba2 (Setup da Semana): pick a date, pick a shift, set headcount override, save/delete; existing overrides displayed per week.
- `slot_config` patching in aba3 before solver call: fetches overrides for the week, shallow-copies and patches headcount values without mutating session state.

### Files Modified
- `database.py`
- `app.py`

---

## 2026-11-07 — Phase 9: Persistent shift and weekly configuration

### Added
- `ShiftTemplates` table and dual-backend CRUD with tenant scoping, default seeding, editable times, closing flags, headcount, and optional priority.
- `WeeklySetup` table and helpers to save weekly overrides without duplicating employee master data.
- `🕒 Configurações` tab for editing active shifts and required headcount.

### Changed
- Weekly setup now loads the latest saved tenant configuration and persists a labelled week on confirmation.
- Roster generation loads `turnos_padrao` and `slot_config` from `ShiftTemplates`, preserving the solver API and fallback defaults.
- Removed the Tab 3 headcount expander because headcount configuration now lives in Configurações.

### Files Modified
- `database.py`
- `app.py`
- `docs/CURRENT_STATE.md`
- `docs/ARCHITECTURE.md`

---

## 2026-11-06 — Landing page exploration: style + layout + serif redesign

### Added
- `scratchpad/styleboard.html` — 4-tile style comparison board (Night/Ultraviolet, Espresso, Sage, Stark) so user could pick visual direction without full builds. User chose Night/Ultraviolet (black + violet).
- `scratchpad/layouts.html` — 4-tile layout comparison in Night colourway (Números, Split, Manifesto, Feature Grid). User chose Manifesto.
- `scratchpad/landing-manifesto.html` — Full Manifesto layout landing page: giant display headline fills first viewport, sections unfold below (Steps → Product panel → Pricing → FAQ → Close band → Footer). Outfit + Onest sans, violet-black Night palette. Ireland-wide messaging, speed/ease focus (not Dublin/law-heavy).
- `scratchpad/landing-serif.html` — Serif editorial landing: Playfair Display 700 roman + italic violet accent question headline ("Is your roster still eating your Sunday?"), trust bar, editorial sections with eyebrow + big serif statement. Night violet/black palette. Same content angle.
- `tokens.css` + `base.css` — Hallmark Ultraviolet scaffold output (shared tokens + base).

### Changed
- Content strategy pivot confirmed: messaging now Ireland-wide (not Dublin-specific), angle is speed/practicality/customization (not law/WRC compliance as primary hook).
- Hosting/email decisions: Cloudflare Pages (free) for landing; Zoho Mail free tier for custom domain email (`@madfrog.ie`), webmail only.

### Files Modified
- `scratchpad/styleboard.html` (new)
- `scratchpad/layouts.html` (new)
- `scratchpad/landing-manifesto.html` (new)
- `scratchpad/landing-serif.html` (new)
- `tokens.css` (new)
- `base.css` (new)
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`

---

## 2026-11-06 — Design skills + pricing decisions + landing page v1

### Added
- `PRODUCT.md` — Impeccable product truth record: users (Dublin café owners/managers, 5–20 staff), purpose (WTI-compliant auto-scheduler), positioning (11h rest + clopening block + keyholder enforced), brand commitments (Mad Frog), evidence on hand, 5 product principles.
- Three UI/UX design skills installed: **Hallmark** (`nutlope/hallmark`), **Impeccable** (v0.1.18, project-scoped), **Taste Skill** (`design-taste-frontend`). Skills live in `.claude/skills/` and `.agents/skills/`.
- Landing page v1 published as Claude Artifact (dark espresso + copper accent, Cormorant Garant display, DM Sans body). Sections: hero, comparison table, how it works, features, pricing, FAQ, coming-soon Multi-Café Panel, contact.
- GROK (CMO agent) reviewed landing page copy and produced 169-line feedback note. Feedback applied: new hero headline (Variant B — "Is your Sunday Excel roster WRC-safe?"), rewritten CTAs, feature card copy, FAQ section, trust signals.

### Changed
- `docs/ARCHITECTURE.md`: added **Frontend UI/UX Governance** section documenting Hallmark/Impeccable/Taste Skill workflow and when to use each.
- `memory/project_decisions_phase8.md`: added new pricing model decisions confirmed by Maestro — trial 3–7 days (no free tier), add-ons monthly-only, €19.90/mês base, license key architecture, Multi-Café Panel as day-zero launch marketing material.
- `docs/GTM_STRATEGY.md`: pricing reference updated to €19.90/mês (was €20).

### Files Modified
- `PRODUCT.md` (new)
- `docs/ARCHITECTURE.md`
- `docs/CURRENT_STATE.md`
- `memory/project_decisions_phase8.md`

---

## 2026-11-06 — Docs: Architecture sync + Mad Frog Stripe registration

### Changed
- `docs/ARCHITECTURE.md`: added `billing_logic.py` to module map; added `preferencia_turno` to Funcionarios schema; updated employee limit note (dynamic 10/20 via billing_logic); added `Subscriptions` table schema; added **Billing & Subscriptions** section (plans, webhook, Edge Function URL); updated Deployment table with Mad Frog studio, Supabase project ref, Stripe mode, and all required secrets.
- `docs/CURRENT_STATE.md`: Phase 8 status updated to reflect Mad Frog Stripe test mode configured.
- Memory `reference_infra.md`: added Mad Frog studio identity, Stripe account info (test mode, local key location, webhook URL), Supabase project ref, Edge Function secrets.
- Memory `project_decisions_phase8.md`: added Mad Frog Stripe architectural decision (isolated account, test mode active).

### Decision log
- Mad Frog is the official studio brand for all SaaS/APK products.
- Stripe account is standalone and isolated (no Ko-fi or managed intermediary restrictions).
- Secret key stored locally — never committed to git. Added to Streamlit Cloud Secrets manually.

### Files Modified
- `docs/ARCHITECTURE.md`
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`
- `memory/reference_infra.md`
- `memory/project_decisions_phase8.md`

---

## 2026-11-06 — Phase 8: Stripe Webhook (Edge Function)

### Added
- `supabase/functions/stripe-webhook/index.ts` — Supabase Edge Function (Deno/TypeScript) that handles Stripe webhook events:
  - `checkout.session.completed` → INSERT new `Subscriptions` row with `plano='pro'` and `validade` from Stripe `current_period_end`
  - `customer.subscription.deleted` → INSERT new `Subscriptions` row with `plano='free'` (downgrade; app picks latest row via `ORDER BY criado_em DESC`)
  - Verifies webhook signature via `stripe.webhooks.constructEventAsync`
  - Fallback: resolves `tenant_id` from `stripe_subscription_id` lookup if subscription metadata is missing
- `billing_logic.py`: added `subscription_data={"metadata": {"tenant_id": str(tenant_id)}}` to `create_stripe_checkout_session()` — propagates `tenant_id` to Stripe Subscription object metadata, enabling clean lookup in `customer.subscription.deleted`

### Decision log
- Uses INSERT rows (not UPDATE/UPSERT) to preserve subscription history. `get_subscription()` already uses `ORDER BY criado_em DESC LIMIT 1` — no schema change needed.
- Edge Function is on Supabase free tier (500K invocations/month — sufficient for MVP).
- Two required secrets: `STRIPE_WEBHOOK_SECRET` (from Stripe Dashboard → Webhooks) + `STRIPE_SECRET_KEY`. `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are auto-injected by Supabase into Edge Functions.

### Deploy instructions (manual)
1. Install Supabase CLI: `npm i -g supabase`
2. `supabase login` → `supabase link --project-ref nbggytkbrxqhnqvtvbpl`
3. `supabase functions deploy stripe-webhook`
4. Register webhook URL in Stripe Dashboard: `https://nbggytkbrxqhnqvtvbpl.supabase.co/functions/v1/stripe-webhook`
5. Add `STRIPE_WEBHOOK_SECRET` to Supabase Project Settings → Edge Functions secrets.

### Files Modified
- `supabase/functions/stripe-webhook/index.ts` (new)
- `billing_logic.py`
- `docs/CHANGELOG.md`
- `docs/CURRENT_STATE.md`

---

## 2026-11-06 — Phase 8: Billing Gates + Stripe Checkout UI

### Added
- `app.py`: Phase 8 billing layer wired — `import os` + `from billing_logic import is_pro, get_employee_limit, check_feature_gate, create_stripe_checkout_session`.
- `app.py`: `_is_pro` and `_emp_limit` computed per-tenant on every rerun (live subscription check).
- `app.py`: Sidebar **"Upgrade para Pro"** expander for non-superadmin users on free plan — shows feature list, price (€39.90 setup + €20/mês), and "Upgrade Agora" button that calls `create_stripe_checkout_session()`. Graceful `KeyError` fallback when `STRIPE_SECRET_KEY` is not yet set.
- `app.py`: Tab 1 — employee add button now checks `len(df_equipe) >= _emp_limit` before calling `adicionar_funcionario()`. Free plan blocks at 10, Pro at 20. Error message is dynamic.
- `app.py`: Tab 3 — PDF export gated behind `check_feature_gate(TENANT_ID, "pdf_export")`. Free users see "🔒 PDF — Pro" in the export column.
- `app.py`: Tab 3 — Roster History section gated behind `check_feature_gate(TENANT_ID, "roster_history")`. Free users see a lock message; pro users get the full save/load UI.
- `app.py`: Tab 4 — Analytics gated behind `check_feature_gate(TENANT_ID, "analytics")`. Free users see a lock message instead of charts.
- `billing_logic.py`: `except Exception: return {"plano": "free"}` added to `get_subscription()` — graceful fallback when Subscriptions table missing (first run, SQLite dev, PG cold start).
- `database.py`: `Subscriptions` table added to `init_db()` for both PG (`CREATE TABLE IF NOT EXISTS`) and SQLite. Seed row (free plan) inserted for `tenant_id=1` on first run.

### Decision log
- Free plan limit: **10 employees** (billing_logic.get_employee_limit returns 10 for non-pro). Pro plan: 20.
- Billing check at app layer (`app.py`) uses `len(df_equipe)` (cached df) — no extra DB round-trip. `database.py` EMPLOYEE_LIMIT=20 stays as absolute safety net at DB layer.
- Superadmin users bypass the billing sidebar panel (they manage all cafes; each cafe's admin sees the upgrade CTA).
- `create_stripe_checkout_session()` wires €20/mês recurring. €39.90 one-time setup fee not yet wired into Stripe session (Phase 8 continuation).

### Validation
- `python -c "..."` dry-run confirmed: free plan → limit=10; pdf_export, analytics, roster_history all blocked; csv_export, solver open.
- `app.py` syntax check: `ast.parse()` clean.

### Files Modified
- `app.py`
- `billing_logic.py`
- `database.py`
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`

---

## 2026-11-06 — Add-ons A+B: Fairness Score + Preference Weighting in CP-SAT

### Added
- `logic.py`: `preferencia` dict extraction + `contract_groups` dict per contract type, consumed by two new soft objective terms.
- `logic.py`: `preference_cost` — `PREF_PENALTY=60` per anti-preferred shift assignment (`x[e,d,s]`). Manhã employees penalised on afternoon/closing shifts; Tarde employees on morning shifts. Strictly soft: BIG_PENALTY (100,000) ensures coverage always dominates.
- `logic.py`: `fairness_cost` — `FAIRNESS_WEIGHT=10` per minute of hour spread within same contract type. `max_g`/`min_g` auxiliary IntVars bound the spread; solver minimises `spread = max_g - min_g` per group. Never violates C4 (max hours hard constraint).
- `database.py`: `preferencia_turno TEXT DEFAULT 'Sem preferência'` column added to Funcionarios table schema (PG `IF NOT EXISTS` migration + SQLite `try/except` migration).
- `database.py`: `adicionar_funcionario` and `atualizar_funcionario` signatures extended with `preferencia='Sem preferência'` parameter.
- `app.py`: "Preferência de Turno" selectbox (`Sem preferência / Manhã / Tarde`) in both Novo Funcionário and Editar Funcionário forms (Tab 1).
- `app.py`: `tipo_contrato` and `preferencia_turno` forwarded through `inputs_semana` dict (Tab 2) to solver.
- `test_fairness_solver.py`: 3-test validation suite proving hard constraints beat soft preferences.

### Decision log
- Audit confirmed C1–C7 are all hard `model.Add()` constraints — no risk of soft terms compromising them.
- Test 2 result: 1 unassigned closing is a capacity issue (C3: 1 shift/day + only 1 keyholder), not a preference-override — C5 keyholder constraint held.
- Test 3 result: 4.5h spread is structural minimum given keyholder restriction forces Bob onto longer closing shifts. Fairness score worked; asymmetry is inherent to C5.
- Checkpoint tag `checkpoint/pre-fairness-20261106` on commit `988aba0` available for rollback.

### Files Modified
- `logic.py`
- `database.py`
- `app.py`
- `test_fairness_solver.py` (new)
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`

---

## 2026-11-06 — REA Analysis: Timefold + Odoo + ERPNext → Roadmap Add-ons

### Added
- `.claude/commands/auto-sync.md`: Autonomous memory sync directive — self-triggers CURRENT_STATE + CHANGELOG updates after every significant logical block, without waiting for user prompt.
- `docs/ROADMAP.md` — Fase 12: Configurable Shift Templates per tenant (ERPNext ShiftType pattern).
- `docs/ROADMAP.md` — Fase 13: Multi-Location Management with branch-scoped manager role (ERPNext branch RBAC pattern).
- `docs/ROADMAP.md` — Add-on A: Fairness Score (Timefold balance constraint → CP-SAT deviation_e auxiliary variable).
- `docs/ROADMAP.md` — Add-on B: Shift Preference Weighting (Timefold desirability soft penalty → `preferencia_turno` column in Funcionarios).
- `docs/ROADMAP.md` — Add-on C: Clock-In & Variance Tracking (Odoo hr.attendance reconciliation → Attendance table + state machine).
- `docs/ROADMAP.md` — Add-on D: Configurable Constraint Weights (Timefold ConstraintConfiguration → ConstraintConfig table per tenant).

### Decision log
- Add-ons A and B (Fairness Score, Preference Weighting) flagged as IMMEDIATE MVP candidates — small CP-SAT objective additions in logic.py with no new tables except one column on Funcionarios.
- Add-ons C and D flagged as Phase 10+ Premium/Enterprise features — require new DB tables and UI surface area.
- CHANGELOG/CURRENT_STATE are project docs (live in docs/); memory keeps a pointer (project_second_brain.md), not copies. Storing full copies in memory would create stale duplicates.

### Files Modified
- `.claude/commands/auto-sync.md` (new)
- `docs/ROADMAP.md`
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`

---

## 2026-11-06 — Tooling: REA Methodology + Clean Room Design Protocol

### Added
- `.claude/commands/rea-analyze.md`: Custom slash command activating Reverse Engineering Architecture (REA) mode — decomposes competitor features into Core Problem / Logical Mechanism / UX Flow, then produces an original build plan for our Streamlit/OR-Tools stack with a Clean Room Checkpoint.
- `docs/CLEAN_ROOM_RULES.md`: Project-level Clean Room protocol — three rules governing how competitor features are studied and re-implemented (Deconstruction Only, Abstract Translation, Original Execution).

### Changed
- `.claude/commands/maestro-start.md`: Added Clean Room protocol acknowledgement to the boot summary output.

### Files Modified
- `.claude/commands/rea-analyze.md` (new)
- `.claude/commands/maestro-start.md`
- `docs/CLEAN_ROOM_RULES.md` (new)
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`

---

## 2026-11-06 — Phase 8: Billing Logic + GTM Strategy + Subscriptions Table

### Added
- `billing_logic.py` (CODEX): `get_subscription()`, `is_pro()`, `get_employee_limit()`, `check_feature_gate()`, `create_stripe_checkout_session()` — full Phase 8 billing layer; dual-backend psycopg2/sqlite; Stripe Checkout €20/mês inline price_data
- `docs/GTM_STRATEGY.md` (GROK): Full Dublin GTM — acquisition channels (Google Maps, Instagram DMs, walk-ins, RAI, LinkedIn), landing page copy (headline + 3 bullets + CTA), cold email script, WTI vs Excel sales argument + objection table, month-1 metrics funnel, 14-day execution playbook
- `requirements.txt`: `stripe>=7.0.0`
- **Supabase DB**: `Subscriptions` table created (tenant_id FK, plano, validade, stripe_customer_id, stripe_subscription_id, criado_em); seed row tenant_id=1 plano='free'

### Decision log
- Learned correct Maestri agent dispatch mechanics: `maestri list` → `maestri ask --batch` to ALL agents simultaneously; never give user prompts to copy manually
- Always confirm Codex file write approvals immediately with `maestri ask "Codex" "a"`
- Subscriptions table must run as 2 separate queries in Supabase SQL Editor (CREATE TABLE then INSERT) due to PostgreSQL planning order

### Files Modified
- `billing_logic.py` (new)
- `requirements.txt`
- `docs/GTM_STRATEGY.md` (new)
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`

---

## 2026-11-06 — Feat: Password Reset UI + Architecture Docs + Phase 8 Scope

### Added
- `database.py`: `get_all_users()` — returns all Users joined with Cafes.name, ordered by cafe then email; superadmin use only
- `database.py`: `reset_password(email, new_password)` — updates password_hash for any user by email; returns bool
- `app.py`: "🔑 Reset de Password" expander in superadmin sidebar — user selectbox (email + cafe), new password + confirm inputs, 6-char minimum validation, `rp_k` form-reset counter
- `.env.example`: Documents `DATABASE_URL` env var for local dev setup (`.env` already in `.gitignore`)

### Changed
- `docs/ARCHITECTURE.md`: Full rewrite — dual-backend strategy table, all 4 DB table schemas (Cafes, Users, Funcionarios, Rosters), CP-SAT solver diagram with C1–C7 constraints, password reset flow, updated session state keys (11 keys), deployment section
- `docs/ROADMAP.md`: Phase 8 scope clarified — Stripe Checkout + Subscriptions table + feature gating confirmed; License Keys and Stock/Clock-in add-ons explicitly deferred to future phases

### Decision log
- Pricing confirmed: €39.90 setup + €20/mês
- Phase 8 scope narrowed to Stripe only (no premature add-ons)
- GROK GTM prompt deferred until after this session's code ships; pricing now confirmed
- CODEX billing_logic.py deferred — existing `EMPLOYEE_LIMIT` already enforces the 20-employee cap; Stripe schema not yet defined

### Files Modified
- `app.py`
- `database.py`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `.env.example` (new)

---

## 2026-11-06 — Fix: Warning UI Flood & Qua Duplicate Slot

### Fixed
- `logic.py`: WTI break warnings collapsed from 1 line per shift (30+ total) into 2 summary lines: one for >6h shifts (mandatory 30-min break) and one for >4.5h–6h shifts (recommended 15-min break)
- `logic.py`: Floating point false positive `39.00h > 39.00h` — tolerance changed from `1e-9` to `0.05h` (3 min), so solver assignments at exactly the contract maximum no longer fire the "limite excedido" warning
- `app.py`: Duplicate `07:00 - 14:00` slot in Quarta-feira `turnos_padrao` replaced with `08:00 - 16:00` (matching all other weekdays)
- `app.py`: CP-SAT solver status line moved out of the warnings expander and displayed as a standalone `st.info()` banner

### Changed
- `app.py`: Unused `import json` removed

### Files Modified
- `app.py`
- `logic.py`

---

## 2026-11-06 — Feat: OR-Tools CP-SAT Solver

### Added
- `logic.py`: Full rewrite of `gerar_escala_automatica` using Google OR-Tools CP-SAT solver
  - Boolean variable matrix `x[e, d, s]` and `unassigned[d, s]` for every employee/day/shift triple
  - Hard constraints: coverage (C1), availability (C2), 1 shift/day (C3), max contract hours in minutes (C4), keyholder on closing (C5), WTI clopening 11h rest (C6), novato max 1 per opening/closing block per day (C7)
  - Objective: `BIG_PENALTY(100k) × unassigned + Σ(over + under)` per employee vs target hours
  - Solver time limit: 10 seconds (`max_time_in_seconds`)
  - Returns `(pd.DataFrame, list[str])` — signature unchanged, drop-in replacement
- `requirements.txt`: `ortools>=9.8.0`
- 8 demo employees inserted into Supabase tenant_id=1 for UI testing (Cristina, Franco, Maria, João, Sara, Liam, Pedro, Natalie)

### Files Modified
- `logic.py`
- `requirements.txt`

---

## 2026-11-06 — Perf: DB Caching & Session Guard

### Changed
- `app.py`: `init_db()` now runs once per browser session (guarded by `session_state['db_initialized']`), not on every Streamlit rerun — saves 1–2 s on Supabase (6+ round-trip DDL statements eliminated per click)
- `app.py`: Added `@st.cache_data` wrappers `_cached_cafe(ttl=300)`, `_cached_funcionarios(ttl=60)`, `_cached_rosters(ttl=30)` — avoids new psycopg2 connections on every rerender
- `app.py`: `equipe_v` and `roster_v` version counters in `session_state` incremented after every write (add/edit/desativar/salvar/deletar) to bust cache without stale data

### Files Modified
- `app.py`

---

## 2026-11-05 — Phase 7: Supabase/PostgreSQL Migration

### Added
- `database.py`: Full dual-backend rewrite — `_PG = bool(os.environ.get('DATABASE_URL'))` flag; `_P = '%s' if _PG else '?'` placeholder; `_get_conn()` returns psycopg2 (RealDictCursor) or sqlite3 based on flag
- `database.py`: Separate CREATE TABLE SQL blocks for PG (SERIAL, NOW()::TEXT, BOOLEAN DEFAULT TRUE) vs SQLite (AUTOINCREMENT, datetime('now'), BOOLEAN DEFAULT 1)
- `database.py`: PG safe migrations via `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`; SQLite migrations via try/except OperationalError
- `database.py`: `RETURNING id` for PG INSERTs; `cursor.lastrowid` for SQLite — both return new row id
- `requirements.txt`: `psycopg2-binary>=2.9.0`

### Changed
- Supabase project created; Transaction pooler URL (IPv4, Frankfurt) set as `DATABASE_URL` in Streamlit Cloud Secrets
- App confirmed live and authenticated at Streamlit Cloud

### Files Modified
- `database.py`
- `requirements.txt`

---

## 2026-11-05 — Phase 7 Prep + Algorithm Rewrite + UX Fixes

### Added
- `database.py`: `nivel TEXT DEFAULT 'experiente'` column on Funcionarios (PG: `ADD COLUMN IF NOT EXISTS`; SQLite: try/except)
- `database.py`: `adicionar_funcionario` / `atualizar_funcionario` accept `nivel` param
- `app.py` Tab 1: `nivel` selectbox (experiente/novato) in Novo Funcionário and Editar forms; `nivel` column shown in employee table
- `app.py` Tab 2: `"nivel"` passed through to `config_semana` per employee
- `logic.py`: Novato constraint — max 1 novato per opening block and per closing block per day (`novato_opening_today` / `novato_closing_today` flags)
- `logic.py`: `closing_count` dict tracks closing shifts per employee across the week
- `logic.py`: `_remaining_avail_days(employee, from_day_index)` helper counts future available days
- `logic.py`: 4-key urgency sort — restricted availability first → closing_count balance → urgency ratio (hours_needed / remaining_days) → minimum hours deficit
- `logic.py`: 08:00-16:00 auto-drop when available staff count < number of shifts for the day
- `app.py` sidebar: `nc_k` counter resets "Registrar Novo Cafe" form fields after successful submission
- `app.py` Tab 1: "Até" time defaults to 18:15 in Específico availability selector

### Files Modified
- `app.py`
- `database.py`
- `logic.py`

---

## 2026-11-05 — Phase 6: RBAC, Commercial Limits & Ajuda Tab

### Added
- `database.py`: `role` column on Users; `superadmin` role seeded for `admin@cafe.com`; migration upgrades existing admin seed to superadmin
- `database.py`: `EMPLOYEE_LIMIT = 20`; `adicionar_funcionario` raises `ValueError("limite_funcionarios:20")` when limit reached
- `app.py`: Auth gate — only `superadmin` role sees "Registrar Novo Cafe" expander in sidebar
- `app.py` Tab 1: Catches `limite_funcionarios` ValueError and shows user-friendly error message
- `app.py` Tab 5 (Ajuda): Full help tab with onboarding guide, availability table, scheduler rules, WTI rules, and FAQ

### Changed
- `app.py` login UI: Gradient card (purple/indigo) with styled form; Register tab removed — user creation is superadmin-only via sidebar
- `database.py`: Seed migration step upgrades role 'admin' → 'superadmin' for admin@cafe.com on every `init_db()` (idempotent)

### Files Modified
- `app.py`
- `database.py`

---

## 2026-11-05 — Phase 5: PDF/Excel Export, Warning Severity & Analytics Tab

### Added
- `logic.py`: `gerar_pdf_escala(roster_df, cafe_nome, semana_label) -> bytes` — landscape A4 PDF with styled header, alternating day shading, Latin-1 encoding for Portuguese characters; uses `fpdf` 1.7.2
- `app.py` Tab 3: **⬇️ Exportar Escala** collapsible expander with 3 download buttons — 📄 CSV, 📊 Excel (`openpyxl`), 🖨️ PDF — replacing the single CSV button
- `app.py` Tab 3: Warning categorization — groups `constraints_warnings` into errors / warnings / infos; expander label shows counts; expander auto-expands when errors exist; uses `st.error` / `st.warning` / `st.info` per severity
- `app.py` Tab 4: **📊 Análise** tab with 4 KPI metrics (Total de Turnos, Preenchidos, Gaps, Cobertura %), Horas por Funcionário vs. Alvo bar chart, and Cobertura por Dia stacked bar chart

### Changed
- `app.py` Tab 3: 4-column action button row → clean 3-column row (Esqueleto Vazio, Gerar Automática, Resetar Aba); exports moved to dedicated expander
- `app.py` Tab 3: `_last_semana_label` now saved to `session_state` on roster save so PDF export can include the week label

### Files Modified
- `app.py`
- `logic.py`
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`

---

## 2026-11-05 — Phase 5: Break-time Warnings, Export CSV & Roster History

### Added
- `logic.py` post-gen: break-time warnings per assigned shift — >6h triggers WTI mandatory 30-min pause; >4.5h triggers recommended 15-min pause
- `app.py` Tab 2: conflict validation on form submit — warns if the same day is marked as both Folga (or Férias) and Treinamento; blocks save until resolved
- `app.py` Tab 3: **⬇️ Exportar CSV** button — enabled when a roster exists, disabled otherwise; downloads `escala.csv` via `st.download_button`
- `database.py`: `Rosters` table (`id, tenant_id, semana, dados_json, criado_em`) created in `init_db`
- `database.py`: `salvar_roster`, `get_rosters`, `get_roster_by_id`, `deletar_roster` CRUD functions
- `app.py` Tab 3: **💾 Histórico de Escalas** section — save current roster with a week label, list saved rosters, 📂 load or 🗑️ delete each entry

### Files Modified
- `app.py`
- `database.py`
- `logic.py`
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`

---

## 2026-11-05 — Phase 4: Weekly Overrides, Training Hours & Soft Hour Tolerance

### Added
- `app.py` Tab 2: global `margem_horas` number input (default 2h) — configures the per-employee soft tolerance band around `horas_alvo`
- `app.py` Tab 2: per-employee multiselects for 🏖️ Folga, ✈️ Férias, 📚 Treinamento days + `H. Treino` total hours input — stored in `config_semana` as `dias_folga`, `dias_ferias`, `dias_treinamento`, `horas_treinamento`
- `app.py` Tab 2: `horas_min` and `horas_max` from DB now passed through to `config_semana` so the scheduler enforces contract limits correctly
- `logic.py` `available()`: weekly override checks — returns False if the day is in `dias_folga`, `dias_ferias`, or `dias_treinamento`
- `logic.py` `gerar_escala_automatica`: training hours pre-loaded into `assigned_hours` before shift scheduling, counting against the weekly total
- `logic.py` `gerar_escala_automatica`: soft tolerance warnings — fires when total hours fall outside `[target − margem, target + margem]` without breaching the hard contract max/min
- `app.py` Tab 3 hours panel: training hours added to per-employee totals; margem used as threshold for red/blue/green status; label shows `± margem`

### Changed
- `app.py` `render_availability_selector`: "Folga" and "Férias" removed from Tab 1 options — these are now weekly-only via Tab 2; backward-compat maps legacy DB values to "Indisponível"
- `logic.py` `gerar_escala_automatica` signature: `margem_horas: float = 2.0` parameter added
- `app.py` Tab 3 auto button: passes `st.session_state['margem_horas']` (default 2.0) to `gerar_escala_automatica`

### Files Modified
- `app.py`
- `logic.py`
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`

Chronological log of major updates. Most recent first.

---

## 2026-11-05 — Phase 4: Folga/Férias + WTI Labour Constraints

### Added
- `app.py` `render_availability_selector`: "Folga" and "Férias" added to `opcoes` list; list reordered to `["Livre", "Só Manhã", "Só Tarde", "Indisponível", "Folga", "Férias", "Específico"]`; index defaults replaced with dynamic `opcoes.index()` calls to avoid brittle hardcoded offsets
- `logic.py` `available()`: "Folga" and "Férias" now treated as unavailable alongside "Indisponível"
- `logic.py` `gerar_escala_automatica`: WTI 11-hr rest rule enforced at candidate-filter time — tracks `prev_day_last_end` per employee across days; blocks assignments where gap to previous day's last shift end < 660 min
- `logic.py` post-gen check: warns if any employee is assigned all 7 days with no rest day (WTI minimum 1 day off per week)

### Files Modified
- `app.py`
- `logic.py`
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`

---

## 2026-11-05 — Phase 4: UX Fixes & Edit Form Refactor

### Fixed
- `app.py` Edit form ("Editar ou Remover") refactored to remove `st.form` wrapper — availability selectbox changes now trigger immediate rerun so the "Específico" time input appears/disappears on selection without needing to submit
- Employee-specific widget keys (`ed_{nome}_*`) prevent state collision when switching between employees in the edit panel
- `form_submit_button` → regular `st.button` with explicit keys for Salvar and Desativar

### Changed
- `app.py` "Novo Funcionário" form: `clear_on_submit=False` → `True` so form clears after cadastro
- `app.py` `render_availability_selector`: added `placeholder="ex: 09:00 - 17:00"` and `help` text to the time `text_input`
- `app.py` sidebar: "➕ Registrar Novo Cafe" expander added to authenticated sidebar (previously only accessible from the login screen)
- `app.py` turnos_padrao and str.contains filter: "Fecho" → "Fechamento" across all 21 shift strings and the keyholder filter
- `logic.py` `calcular_horas_turno` docstring and `pode_trabalhar` check: "Fecho" → "Fechamento"

### Files Modified
- `app.py`
- `logic.py`
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`

---

## 2026-11-05 — Phase 4: Codex Scheduler Integration

### Changed
- `gerar_escala_automatica` in `logic.py` fully replaced with Codex algorithm
  - New signature: `(config_semana, turnos_padrao) -> (pd.DataFrame, list[str])`
  - Closing shifts now detected by end-time > 17:00 (not by keyword "Fecho")
  - Clopening guard: opening shifts block employees who closed the previous day
  - Post-generation checks: keyholder-on-closing, weekly hour limits (min/max), clopening cross-day validation
  - `numeric_value` helper resolves multiple field-name aliases (horas_alvo, horas_max, etc.)
- `app.py` Tab 3 updated to consume new return tuple
  - `constraints_warnings` stored in `st.session_state`
  - `⚠️ Avisos de Regras Trabalhistas` expander renders after roster; clopening/keyholder/hour violations shown as `st.error`, others as `st.warning`
  - Reset button now clears `constraints_warnings` alongside `roster_df`

### Added
- `import pandas as pd` at module level in `logic.py`
- `.gitignore` (excludes `*.db`, `__pycache__/`, `.env`, `.maestri/`)
- Git repository initialized at project root

### Files Modified
- `logic.py`
- `app.py`
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`
- `.gitignore` (new)

---

## 2026-11-05 — Phase 3: Authentication System

### Added
- `Users` table in SQLite: `id`, `tenant_id`, `email`, `password_hash`, `role`, `created_at`
- `_hash_password(password)` — 16-byte random salt + SHA-256, stored as `salt_hex:hash_hex`
- `_check_password(password, stored)` — constant-time-safe reconstruction and comparison
- `create_user(tenant_id, email, password, role)` in `database.py`
- `verify_credentials(email, password)` in `database.py` — returns user dict or None
- `get_cafe_by_id(cafe_id)` in `database.py` — returns cafe dict for sidebar display
- Auth gate in `app.py`: Login and Register tabs; `st.stop()` blocks unauthenticated rendering
- Authenticated sidebar: cafe name, user email, role badge, Logout button
- Default seed: `admin@cafe.com` / `admin123` created on first `init_db()` run

### Changed
- `app.py` imports updated; old `tenant_id = 1` bootstrap replaced by auth gate
- `TENANT_ID` now sourced from `st.session_state['tenant_id']` set during login

### Files Modified
- `database.py`
- `app.py`

---

## 2026-11-05 — Phase 2: Multi-Tenancy

### Added
- `Cafes` table: `id`, `name`, `admin_email`, `created_at`
- `tenant_id` FK column on `Funcionarios` — added via safe `ALTER TABLE` migration
- `get_cafes()`, `criar_cafe(name, admin_email)` in `database.py`
- Default tenant seeded: `id=1, name="Default Cafe"` on first `init_db()`

### Changed
- All CRUD functions (`get_funcionarios_ativos`, `adicionar_funcionario`, `atualizar_funcionario`, `desativar_funcionario`) now require `tenant_id` as first parameter
- UPDATE/DELETE queries include `AND tenant_id = ?` cross-tenant write guard
- `app.py` bootstrapped `st.session_state['tenant_id'] = 1` as placeholder for future auth

### Files Modified
- `database.py`
- `app.py`

---

## 2026-11-05 — Phase 1: Modularisation

### Added
- `database.py` — all SQLite connection logic, table creation, and CRUD functions
- `logic.py` — pure business logic: `calcular_horas_turno`, `pode_trabalhar`, `gerar_escala_automatica`

### Changed
- `app.py` refactored to Streamlit UI only — imports from `database.py` and `logic.py`
- `pode_trabalhar` extracted from inline closure in Tab 3 button handler to standalone function in `logic.py`
- `gerar_escala_automatica` extracted to `logic.py` — now a testable, Streamlit-free function
- `render_availability_selector` retained in `app.py` (uses `st.*` widgets — not pure logic)

### Files Modified
- `app.py` (rewritten)
- `database.py` (new)
- `logic.py` (new)
