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
Monetização do Micro-SaaS.

- [ ] Integrar Stripe Checkout para planos mensais
- [ ] Tabela `Subscriptions` (tenant_id, plano, validade, stripe_customer_id)
- [ ] Bloquear funcionalidades avançadas (PDF, Analytics, histórico) para plano Free
- [ ] Webhook Stripe para atualizar estado da subscrição automaticamente
- [ ] Página de gestão de plano no sidebar do superadmin

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

## Notas de Arquitetura

- **DB migration path:** SQLite → Supabase; apenas `database.py` muda
- **Deploy:** Streamlit Community Cloud (nandocaetano/roster-cafe · main · app.py)
- **Limite atual:** 20 funcionários por tenant (configurável em `EMPLOYEE_LIMIT` em `database.py`)
- **Autenticação:** SHA-256 + salt; futuro — considerar migração para Supabase Auth
