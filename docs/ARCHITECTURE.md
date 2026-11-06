# Architecture

---

## Module Map

```
┌──────────────────────────────────────────────────────────────────┐
│                           app.py                                  │
│  Streamlit UI — 5 tabs + auth gate + sidebar                      │
│                                                                    │
│  • Auth gate (Login)                                               │
│  • Sidebar: cafe name, email, role, logout                         │
│           superadmin: Registrar Novo Cafe, Reset de Password       │
│  • Tab 1 — Gestão do Time  (employee CRUD + availability)          │
│  • Tab 2 — Setup da Semana (weekly overrides: folga/férias/treino) │
│  • Tab 3 — Rascunho e Aprovação (roster editor + history + export) │
│  • Tab 4 — Análise (coverage metrics + hours chart)                │
│  • Tab 5 — Ajuda (documented rules + workflow guide)               │
│                                                                    │
│  Caching: @st.cache_data wrappers with version-counter bust        │
│    _cached_cafe(cafe_id, _v)         ttl=300s                      │
│    _cached_funcionarios(tid, _v)     ttl=60s                       │
│    _cached_rosters(tid, _v)          ttl=30s                       │
│                                                                    │
│  Imports ────────────────────────────────────────────────────────► │
│          database.py                   logic.py                    │
└──────────────────────────────────────────────────────────────────┘

┌────────────────────────────┐   ┌──────────────────────────────────┐
│        database.py          │   │            logic.py               │
│  Dual-backend CRUD layer    │   │  Pure Python — no I/O             │
│  • _PG flag (DATABASE_URL)  │   │  • calcular_horas_turno()         │
│  • _get_conn() factory      │   │  • pode_trabalhar()               │
│  • init_db() + migrations   │   │  • gerar_escala_automatica()      │
│  • criar_cafe()             │   │    └─ OR-Tools CP-SAT solver       │
│  • get_cafe_by_id()         │   │       x[e,d,s] BoolVar matrix     │
│  • create_user()            │   │       Hard constraints C1–C7       │
│  • verify_credentials()     │   │       BIG_PENALTY objective        │
│  • get_all_users()          │   │       10s time limit               │
│  • reset_password()         │   │  • gerar_pdf_escala() (fpdf)       │
│  • get_funcionarios_ativos()│   │                                    │
│  • adicionar_funcionario()  │   │  No streamlit. No DB imports.      │
│  • atualizar_funcionario()  │   │  Fully unit-testable.              │
│  • desativar_funcionario()  │   └──────────────────────────────────┘
│  • salvar_roster()          │
│  • get_rosters()            │
│  • get_roster_by_id()       │
│  • deletar_roster()         │
└────────────────────────────┘
```

---

## Dual-Backend Strategy

| Environment | DB | Connection |
|---|---|---|
| Streamlit Cloud (prod) | PostgreSQL via Supabase | `DATABASE_URL` env var → psycopg2 |
| Local dev | SQLite | `roster_cafe.db` created at runtime (not committed) |

```python
_PG = bool(os.environ.get('DATABASE_URL'))  # True on cloud
_P  = '%s' if _PG else '?'                 # SQL placeholder
```

For local dev, copy `.env.example` to `.env` and fill in `DATABASE_URL` if testing against Supabase.

---

## Database Tables (PostgreSQL / SQLite)

### `Cafes`
| Column | Type | Notes |
|---|---|---|
| id | SERIAL / AUTOINCREMENT PK | Tenant identifier |
| name | TEXT NOT NULL | Display name |
| admin_email | TEXT | Contact email |
| created_at | TEXT | ISO-8601 UTC timestamp |

**Seed row:** `id=1, name="Default Cafe", admin_email="admin@cafe.com"`

---

### `Users`
| Column | Type | Notes |
|---|---|---|
| id | SERIAL / AUTOINCREMENT PK | |
| tenant_id | INTEGER FK → Cafes.id | Scopes user to a cafe |
| email | TEXT NOT NULL UNIQUE | Login identifier |
| password_hash | TEXT NOT NULL | `salt_hex:sha256_hex` (16-byte salt) |
| role | TEXT DEFAULT 'admin' | `superadmin` / `admin` |
| created_at | TEXT | ISO-8601 UTC timestamp |

**Seed row:** `email="admin@cafe.com"`, role=`superadmin`, tenant_id=1 (password set at first deploy, reset via Password Reset UI).

---

### `Funcionarios`
| Column | Type | Notes |
|---|---|---|
| id_funcionario | SERIAL / AUTOINCREMENT PK | |
| tenant_id | INTEGER FK → Cafes.id NOT NULL DEFAULT 1 | Multi-tenancy FK |
| nome | TEXT NOT NULL | |
| cargo | TEXT NOT NULL | Manager / Assistant Manager / Head Barista / Barista |
| tipo_contrato | TEXT NOT NULL | Full-time / Part-time |
| horas_min | INTEGER | Weekly minimum hours |
| horas_max | INTEGER | Weekly maximum hours |
| d_seg … d_dom | TEXT | Availability: Indisponível / Livre / Só Manhã / Só Tarde / Específico: HH:MM–HH:MM |
| status_ativo | BOOLEAN DEFAULT TRUE | Soft-delete flag |
| nivel | TEXT DEFAULT 'experiente' | `experiente` / `novato` — CP-SAT novato constraint |

**Limit:** `EMPLOYEE_LIMIT = 20` active employees per tenant (enforced in `adicionar_funcionario`).

---

### `Rosters`
| Column | Type | Notes |
|---|---|---|
| id | SERIAL / AUTOINCREMENT PK | |
| tenant_id | INTEGER FK → Cafes.id NOT NULL | |
| semana | TEXT NOT NULL | User-defined label (e.g. "Semana 47 — Nov 2026") |
| dados_json | TEXT NOT NULL | Full roster as JSON (`orient="records"`) |
| criado_em | TEXT NOT NULL | ISO-8601 UTC timestamp |

---

## CP-SAT Scheduler (logic.py)

Replaces the previous greedy urgency-sort algorithm as of 2026-11-06.

```
OR-Tools CP-SAT solver
  Variables:   x[e, d, s]        BoolVar — employee e works shift s on day d
               unassigned[d, s]  BoolVar — shift has no cover
  Hard constraints:
    C1  Coverage         — Σ x[e,d,s] + unassigned[d,s] == 1
    C2  Availability     — x[e,d,s] == 0 if employee unavailable
    C3  One shift/day    — Σ_s x[e,d,s] <= 1
    C4  Contract hours   — total assigned minutes + training <= max_hours * 60
    C5  Keyholder        — only Manager/Asst Mgr/Head Barista on closing shifts
    C6  WTI clopening    — 11h rest gap enforced between close and next-day open
    C7  Novato limit     — max 1 novato per opening block and per closing block per day
  Objective:   MIN  100,000 × Σ unassigned  +  Σ |assigned_hours - target_hours|
  Time limit:  10 seconds
```

Post-solve warnings are summarised (not per-shift):
- WTI >6h: one summary line (mandatory 30-min break)
- WTI >4.5h–6h: one summary line (recommended 15-min break)
- CP-SAT solver status shown as `st.info()` banner, not inside warnings expander

---

## Data Flows

### Auth flow
```
Browser → email/password → st.form submit
  → verify_credentials(email, password)   [database.py]
  → st.session_state['user'] = user dict
  → st.session_state['tenant_id'] = user['tenant_id']
  → st.rerun() → main app renders
```

### Password reset flow (superadmin only)
```
Sidebar → 🔑 Reset de Password expander
  → get_all_users()                        [database.py] — all users + cafe name
  → selectbox: pick user by email (cafe)
  → new password input + confirm
  → reset_password(email, new_password)    [database.py] — UPDATE Users SET password_hash
```

### Auto-schedule flow
```
Tab 2 → Confirm Horas da Semana
  → st.session_state['config_semana'] = {nome: {vai_trabalhar, horas_alvo, cargo, nivel, disponibilidade, ...}}

Tab 3 → Gerar Escala Automática
  → gerar_escala_automatica(config_semana, turnos_padrao)   [logic.py]
      → CP-SAT model: build variables, constraints, objective
      → solver.Solve() — max 10s
      → extract solution, generate post-solve warnings
      → return (DataFrame, list[str])
  → st.session_state['roster_df'] = DataFrame
  → st.session_state['constraints_warnings'] = warnings
  → st.info() banner: CP-SAT status
  → st.expander: categorised warnings (erros / avisos / infos)
```

---

## Password Security

Algorithm: **SHA-256 with 16-byte random salt**

```python
salt = os.urandom(16)
hash = sha256(salt + password.encode('utf-8')).hexdigest()
stored = f"{salt.hex()}:{hash}"
```

> Upgrade path: replace `_hash_password` / `_check_password` in `database.py` with `bcrypt` or `argon2-cffi` — no other files change.

---

## Session State Keys

| Key | Set by | Purpose |
|---|---|---|
| `user` | auth gate on login | Dict: id, tenant_id, email, role |
| `tenant_id` | auth gate on login | Active tenant scope for all DB calls |
| `db_initialized` | app startup | Guards `init_db()` to run once per browser session |
| `equipe_v` | Tab 1 writes | Cache-bust counter for `_cached_funcionarios` |
| `roster_v` | Tab 3 writes | Cache-bust counter for `_cached_rosters` |
| `config_semana` | Tab 2 form submit | Weekly hours/availability snapshot |
| `margem_horas` | Tab 2 form submit | Hour tolerance for scheduler warnings |
| `roster_df` | Tab 3 generate buttons | Current editable roster DataFrame |
| `constraints_warnings` | Tab 3 auto-generate | CP-SAT post-solve warning list |
| `nc_k` | superadmin sidebar | Form reset counter for Registrar Novo Cafe |
| `rp_k` | superadmin sidebar | Form reset counter for Reset de Password |
| `novo_k` | Tab 1 | Form reset counter for Novo Funcionário |

---

## Deployment

| Item | Value |
|---|---|
| Repo | github.com/nandocaetano/roster-cafe |
| Branch | master → Streamlit Cloud watches master |
| Platform | Streamlit Community Cloud (free tier, ~1GB RAM) |
| Secrets | `DATABASE_URL` set in Streamlit Cloud Settings → Secrets |
| Local dev | Copy `.env.example` → `.env`, fill DATABASE_URL |
