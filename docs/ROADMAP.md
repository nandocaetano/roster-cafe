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
Monetização do Micro-SaaS. Pricing: **€39.90 setup (one-time) + €20/mês**.

**Scope confirmado:**
- [ ] Tabela `Subscriptions` (tenant_id, plano, validade, stripe_customer_id, stripe_subscription_id)
- [ ] Integrar Stripe Checkout para planos mensais (€20/mês)
- [ ] Webhook Stripe para atualizar `Subscriptions` automaticamente (paid / cancelled / past_due)
- [ ] Feature gating: bloquear PDF export, Analytics (Tab 4) e Roster History para plano Free
- [ ] Página de gestão de plano no sidebar do superadmin

**Fora do scope desta fase (re-avaliar em fases futuras):**
- License Keys — incompatível com modelo web SaaS multi-tenant
- Add-ons Stock / Clock-in — módulos não definidos; implementar só após Phase 8 completa

---

## Próximo

### Fase 9 — Mobile UX & Progressive Web App
App usável no telemóvel pelos managers do café.

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

### Fase 12 — Configurable Shift Templates *(REA: ERPNext)*
Replace hardcoded `turnos_padrao` dict with a per-tenant `ShiftTemplates` DB table.

- [ ] `ShiftTemplates` table: `{id, tenant_id, name, start_time, end_time, is_keyholder_required}`
- [ ] Tab 3 UI: manager edits their own shift templates instead of using hardcoded defaults
- [ ] CP-SAT solver reads templates from DB instead of from `app.py` constant
- [ ] **Origin:** ERPNext `ShiftType` entity pattern — template entity decoupled from assignment

### Fase 13 — Multi-Location Management *(REA: ERPNext)*
Support cafes with multiple branches, each with autonomous rosters and a local manager role.

- [ ] `Locations` table: `{id, tenant_id, name, address}` — sub-units within a Cafe tenant
- [ ] `location_id` FK on `Funcionarios` and `Rosters`
- [ ] New role `location_manager` — scoped to one location, cannot see other branches
- [ ] Superadmin sees aggregate view across all locations
- [ ] **Origin:** ERPNext branch-scoped manager RBAC + ShiftType per branch

### Epic futuro — Demand Prediction Alerts
Sugerir reforço de capacidade com base em sinais externos e eventos locais.

- [ ] Alertas para feriados locais, concertos, gigs e jogos desportivos próximos
- [ ] Sugestão de aumento de headcount por dia/turno, sempre sujeita a aprovação do manager
- [ ] Histórico da recomendação e motivo apresentado no setup semanal
- [ ] Não implementar previsão automática nesta fase; apenas manter o epic no roadmap

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
