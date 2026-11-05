# Architecture

---

## Module Map

```
┌─────────────────────────────────────────────────┐
│                    app.py                        │
│  Streamlit UI                                    │
│  • Auth gate (Login / Register)                  │
│  • Sidebar (cafe name, email, logout)            │
│  • Tab 1 — Gestão do Time                        │
│  • Tab 2 — Setup da Semana                       │
│  • Tab 3 — Rascunho e Aprovação                  │
│                                                  │
│  Imports ──────────────────────────────────────► │
│          database.py           logic.py          │
└─────────────────────────────────────────────────┘

┌────────────────────────┐   ┌──────────────────────────┐
│      database.py       │   │        logic.py           │
│  SQLite CRUD layer     │   │  Pure Python logic        │
│  • init_db()           │   │  • calcular_horas_turno() │
│  • get_cafes()         │   │  • pode_trabalhar()       │
│  • criar_cafe()        │   │  • gerar_escala_auto()    │
│  • get_cafe_by_id()    │   │                           │
│  • create_user()       │   │  No Streamlit imports.    │
│  • verify_credentials()│   │  No DB imports.           │
│  • get_funcionarios()  │   │  Fully unit-testable.     │
│  • adicionar_func()    │   └──────────────────────────┘
│  • atualizar_func()    │
│  • desativar_func()    │
└────────────────────────┘
```

---

## SQLite Tables

### `Cafes`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK AUTOINCREMENT | Tenant identifier |
| name | TEXT NOT NULL | Display name of the cafe |
| admin_email | TEXT | Contact email |
| created_at | TEXT | ISO-8601 UTC timestamp |

**Seed row:** `id=1, name="Default Cafe", admin_email="admin@cafe.com"`

---

### `Users`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK AUTOINCREMENT | |
| tenant_id | INTEGER FK → Cafes.id | Scopes user to a single cafe |
| email | TEXT NOT NULL UNIQUE | Login identifier |
| password_hash | TEXT NOT NULL | `salt_hex:sha256_hex` (16-byte random salt) |
| role | TEXT DEFAULT 'admin' | Future: admin / manager / viewer |
| created_at | TEXT | ISO-8601 UTC timestamp |

**Seed row:** `email="admin@cafe.com", password="admin123"` (hashed), `tenant_id=1`

---

### `Funcionarios`
| Column | Type | Notes |
|---|---|---|
| id_funcionario | INTEGER PK AUTOINCREMENT | |
| tenant_id | INTEGER FK → Cafes.id NOT NULL DEFAULT 1 | Multi-tenancy FK |
| nome | TEXT NOT NULL | |
| cargo | TEXT NOT NULL | Manager / Assistant Manager / Head Barista / Barista |
| tipo_contrato | TEXT NOT NULL | Full-time / Part-time |
| horas_min | INTEGER | Weekly minimum hours |
| horas_max | INTEGER | Weekly maximum hours (target for scheduler) |
| d_seg … d_dom | TEXT | Availability per day: Indisponível / Livre / Só Manhã / Só Tarde / Específico: HH:MM–HH:MM |
| status_ativo | BOOLEAN DEFAULT 1 | Soft-delete flag |

**Migration:** `ALTER TABLE Funcionarios ADD COLUMN tenant_id` runs inside `init_db()` wrapped in `try/except OperationalError` to handle pre-existing databases safely.

---

## Data Flows

### Auth flow
```
Browser → fill email/password → st.form submit
  → verify_credentials(email, password)          [database.py]
      → SELECT user WHERE email = ?
      → _check_password(input, stored_hash)
      → return user dict or None
  → st.session_state['user'] = user
  → st.session_state['tenant_id'] = user['tenant_id']
  → st.rerun()  →  main app renders
```

### Auto-schedule flow
```
Tab 2 → Confirm Horas da Semana
  → st.session_state['config_semana'] = {nome: {vai_trabalhar, horas_alvo, cargo, disponibilidade}}

Tab 3 → Gerar Escala Automática
  → gerar_escala_automatica(config_semana, turnos_padrao)   [logic.py]
      → for each day/shift:
          → pode_trabalhar(nome, turno, dia, config_semana)
          → sort candidates by remaining hours headroom
          → assign keyholder to closing shifts first
      → return ordered list of {Dia, Horário, Funcionário}
  → st.session_state['roster_df'] = DataFrame(result)
  → st.data_editor renders editable roster
  → Dynamic Hours Panel recalculates live from edited rows
  → Keyholder rule check runs on every rerender
```

---

## Password Security

Algorithm: **SHA-256 with 16-byte random salt**

```python
salt = os.urandom(16)                               # 128-bit random salt
hash = sha256(salt + password.encode('utf-8')).hexdigest()
stored = f"{salt.hex()}:{hash}"                     # stored in DB
```

Verification reconstructs the same hash using the stored salt and compares in constant time via string equality.

> Upgrade path: replace `_hash_password` / `_check_password` in `database.py` with `bcrypt` or `argon2-cffi` when moving to production — no other files need changes.

---

## Session State Keys

| Key | Set by | Purpose |
|---|---|---|
| `user` | auth gate on login | Dict with id, tenant_id, email, role |
| `tenant_id` | auth gate on login | Active tenant scope for all DB calls |
| `config_semana` | Tab 2 form submit | Weekly hours/availability config |
| `roster_df` | Tab 3 generate buttons | Current editable roster DataFrame |
