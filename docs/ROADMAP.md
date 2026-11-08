# Roadmap

---

## Concluído

| Fase | Descrição | Status |
|---|---|---|
| 1 | Modularisation — app.py / database.py / logic.py | ✅ |
| 2 | Multi-Tenancy — Cafes table, tenant_id FK, CRUD isolado por tenant | ✅ |
| 3 | Authentication — Users table, SHA-256+salt, login gate, sidebar | ✅ |
| 4 | Algorithm & WTI Constraints — clopening, keyholder, 11h rest, 7-day limit | ✅ |
| 5 | Weekly Overrides + Soft Tolerance — Folga/Férias/Treinamento na Aba 2, margem de horas, break warnings, export CSV/Excel/PDF, Roster History, Analytics Tab 4 | ✅ |
| 6 | RBAC & Commercial Limits — superadmin role, registro público bloqueado, limite 20 funcionários por tenant, login UI card, Aba 5 Ajuda | ✅ |
| 7 | Persistent Database (Supabase/PostgreSQL) — psycopg2 dual-backend, Transaction pooler, DATABASE_URL secret, live on Streamlit Cloud | ✅ |

---

## Ativo

### Fase 8 — Billing & Subscription (Stripe)
Monetização do Micro-SaaS. Pricing: **4 tiers (Starter €19/Standard €39/Plus €65/Network €35) + trial 15 dias com cartão obrigatório. Sem free tier, sem setup fee.**

**Scope confirmado:**
- [x] Tabela `Subscriptions` (tenant_id, plano, validade, stripe_customer_id, stripe_subscription_id)
- [x] Integrar Stripe Checkout — 4 tiers mensais e anuais
- [x] Webhook Stripe Edge Function — INSERT audit trail, tier de session.metadata
- [x] Feature gating: bloqueia PDF export, Analytics, Roster History para plano free
- [ ] **Paywall gate na entrada** — bloquear acesso sem Stripe subscription (sem free tier)
- [ ] **Self-registration** — auto-criar Cafe+User após checkout.session.completed no webhook
- [ ] Preços corretos na UI (sidebar + trial wall)

**Fora do scope desta fase:**
- License Keys — incompatível com modelo web SaaS multi-tenant
- Add-ons Stock / Clock-in — implementar só após Phase 8 completa

---

## Próximo

### Fase 9b — Mobile UX & Progressive Web App
App usável no telemóvel pelos managers do café.
*(Nota: "Fase 9" foi usada para Persistent Shift Configuration — já completa. Esta é a 9b para evitar conflito.)*

- [ ] Substituir seletor de disponibilidade (8 colunas) por toggle grid responsivo
- [ ] Aba 2 reformulada para funcionar em ecrã estreito
- [ ] Meta tags PWA + ícone para "Add to Home Screen"
- [ ] Testar fluxo completo em iOS Safari e Android Chrome

### Fase 10 — Employee Self-Service Portal
Funcionários gerem a própria disponibilidade.

- [ ] Role `employee` na tabela Users
- [ ] Portal próprio: funcionário vê a sua escala da semana e altera disponibilidade
- [ ] Manager aprova alterações antes de regenerar a escala
- [ ] Notificações por e-mail quando a escala é publicada (SendGrid ou Resend)

### Fase 11 — Multi-Week View & Reporting
Visão histórica e relatórios para compliance.

- [ ] Comparativo de horas entre semanas (gráfico de tendência)
- [ ] Relatório mensal por funcionário (horas totais, gaps, avisos WTI)
- [ ] Export PDF do relatório mensal
- [ ] Dashboard superadmin: todos os cafés + métricas agregadas

---

### ~~Fase 12 — Configurable Shift Templates~~ ✅ COMPLETA (entregue na Fase 9)
ShiftTemplates implementado em `database.py` + UI completa em `app.py` (aba "🕒 Shifts"). Solver lê templates da DB via `build_turnos_padrao(tenant_id)`. **Não implementar novamente.**

### Fase 13 — Multi-Location Management *(REA: ERPNext)*
Support cafes with multiple branches, each with autonomous rosters and a local manager role.

- [ ] `Locations` table: `{id, tenant_id, name, address}` — sub-units within a Cafe tenant
- [ ] `location_id` FK on `Funcionarios` and `Rosters`
- [ ] New role `location_manager` — scoped to one location, cannot see other branches
- [ ] Superadmin sees aggregate view across all locations
- [ ] **Origin:** ERPNext branch-scoped manager RBAC + ShiftType per branch

---

## Add-ons Premium (REA-Derived)

> Features extracted via `/rea-analyze` from open-source rostering tools. Build from scratch using our stack — no adapted code.

### Add-on A — Fairness Score *(REA: Timefold)* — IMMEDIATE MVP candidate
Extend CP-SAT objective with an explicit fairness balance term.

- [ ] Add `deviation_e` auxiliary variable per employee in `logic.py`: `deviation_e ≥ assigned_minutes_e − target_minutes_e` and `deviation_e ≥ target_minutes_e − assigned_minutes_e`
- [ ] Add `sum(deviation_e)` as a third objective term with configurable weight
- [ ] Display fairness score in Tab 4 Analytics (gini coefficient or max-spread metric)
- [ ] **Origin:** Timefold `HardSoftScore` fairness balance constraint

### Add-on B — Shift Preference Weighting *(REA: Timefold)* — IMMEDIATE MVP candidate
Allow employees to mark morning/evening preference; CP-SAT penalizes anti-preferred assignments.

- [ ] Add `preferencia_turno` column to `Funcionarios`: `Manhã / Tarde / Sem preferência`
- [ ] Add soft penalty in CP-SAT objective: `+PREFERENCE_PENALTY × x[e,d,s]` when shift type conflicts with preference
- [ ] Tab 1 UI: preference dropdown in employee form
- [ ] **Origin:** Timefold `ShiftAssignment.desirability` soft constraint

### Add-on C — Clock-In & Variance Tracking *(REA: Odoo)* — Phase 10 Premium Feature
Close the loop between planned shifts and actual time worked.

- [ ] `Attendance` table: `{id, tenant_id, employee_id, date, clock_in, clock_out, planned_start, planned_end, variance_minutes, status}`
- [ ] Variance engine in `logic.py`: `variance = actual_duration − planned_duration`; `overtime_flag = variance > grace_period`
- [ ] State machine per `(employee, date)`: `Planned → Present | Absent | Late | Overtime`
- [ ] Manager variance table in Tab 4; export to CSV/PDF
- [ ] **Origin:** Odoo `hr.attendance` + `hr.planning.slot` reconciliation pattern

### Add-on D — Configurable Constraint Weights *(REA: Timefold)* — Enterprise Tier
Manager-tunable soft constraint weights stored per tenant.

- [ ] `ConstraintConfig` table: `{tenant_id, fairness_weight, preference_weight, hour_balance_weight}`
- [ ] Tab 5 Ajuda or new Settings tab: sliders for each weight (Pro/Enterprise plans only)
- [ ] CP-SAT objective reads weights from DB at schedule generation time
- [ ] **Origin:** Timefold `ConstraintConfiguration` entity pattern

---

## Notas de Arquitetura

- **DB migration path:** SQLite → Supabase; apenas `database.py` muda
- **Deploy:** Streamlit Community Cloud (nandocaetano/roster-cafe · main · app.py)
- **Limite atual:** 20 funcionários por tenant (configurável em `EMPLOYEE_LIMIT` em `database.py`)
- **Autenticação:** SHA-256 + salt; futuro — considerar migração para Supabase Auth
