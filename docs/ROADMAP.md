# Roadmap

---

## Completed

### Phase 1 — Modularisation
Split the monolithic single-file Streamlit app into three clean modules:
- `database.py` — all SQLite connection and CRUD logic
- `logic.py` — pure business logic (shift math, availability, auto-scheduler)
- `app.py` — Streamlit UI only, imports from the two modules above

### Phase 2 — Multi-Tenancy
Added full tenant isolation so the platform can serve multiple independent cafes:
- `Cafes` table with id, name, admin_email, created_at
- `tenant_id` FK column on `Funcionarios` (safe ALTER migration for existing DBs)
- All CRUD functions require `tenant_id`; UPDATE/DELETE include `AND tenant_id = ?` guard
- Default tenant seeded at `id = 1`

### Phase 3 — Authentication
Secure login system gating access to the full app:
- `Users` table with per-tenant scope, SHA-256 + salt password hashing
- `create_user`, `verify_credentials`, `get_cafe_by_id` helpers in `database.py`
- Login / Register tabs in Streamlit; `st.stop()` blocks unauthenticated access
- Authenticated sidebar: cafe name, user email, role badge, Logout button
- Default seed: `admin@cafe.com` / `admin123` on first run

---

## Active

### Phase 4 — Algorithm Optimization & Irish Labour Constraints
Improve the auto-scheduler's correctness and compliance:

- [ ] Encode Irish Working Time Act rules (WTI):
  - Max 48 hrs/week averaged over 4 months
  - Max 8 hrs/day for night workers
  - Min 11 hrs rest between shifts
  - Min 24 hrs rest per 7-day period
  - Breaks: 15 min after 4.5 hrs, 30 min after 6 hrs
- [ ] Add `validar_turno(nome, turno, dia, config_semana)` to `logic.py`
- [ ] Surface violations in Tab 3 "Avisos de Regras" alongside existing keyholder check
- [ ] Optionally score and rank scheduler candidates by constraint compliance

---

## Upcoming

### Phase 5 — Roster History & Export
- Save approved rosters to a `Rosters` table (tenant-scoped)
- Week selector to browse past schedules
- Export to PDF / CSV

### Phase 6 — Role-Based Access Control
- Extend `Users.role` to: `admin`, `manager`, `viewer`
- Managers can generate and edit rosters; viewers can only read
- Restrict destructive actions (desativar_funcionario, etc.) to admin/manager

### Phase 7 — Production Database Migration
- Replace SQLite with PostgreSQL (or Supabase)
- Swap `sqlite3` calls in `database.py` for `psycopg2` / SQLAlchemy — zero changes to `logic.py` or `app.py`
- Add connection pooling

### Phase 8 — Notifications & Alerts
- Email shift summaries to employees
- Push alerts for keyholder gaps or budget overrun
