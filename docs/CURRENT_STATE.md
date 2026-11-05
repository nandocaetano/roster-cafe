# Current State

> Single source of truth. Update this file at the end of every session.

---

## Active Phase

**Phase 4 — Algorithm Optimization & Irish Labour Constraints**

---

## Completed Phases

| Phase | Description | Status |
|---|---|---|
| 1 | Modularisation — split monolithic app.py into app.py / database.py / logic.py | ✅ Complete |
| 2 | Multi-Tenancy — Cafes table, tenant_id FK on Funcionarios, all CRUD scoped by tenant | ✅ Complete |
| 3 | Authentication — Users table, SHA-256 + salt hashing, Login/Register UI, session auth gate, sidebar with logout | ✅ Complete |
| 4 | Algorithm Optimization & Irish Labour Constraints | 🔄 Active |

---

## Modified Files (last session)

| File | Last Change |
|---|---|
| `app.py` | Folga/Férias removed from Tab 1 opcoes (backward-compat maps to Indisponível); Tab 2 gains `margem_horas` global field + per-employee Folga/Férias/Treinamento multiselects + H. Treino input; Tab 3 passes margem to scheduler and includes training hours in hours panel |
| `logic.py` | `gerar_escala_automatica` accepts `margem_horas` param; `available()` blocks days in dias_folga/ferias/treinamento; training hours pre-loaded into `assigned_hours`; soft tolerance warnings added to post-gen checks |

---

## Current Architecture Snapshot

```
app_escala/
├── app.py          # Streamlit UI only — tabs 1/2/3 + auth gate + sidebar
├── database.py     # SQLite CRUD — Cafes, Users, Funcionarios
├── logic.py        # Pure Python — shift math, availability checks, auto-scheduler
├── roster_cafe.db  # SQLite database (created at runtime)
└── docs/           # This Second Brain
```

---

## Blockers

_None currently recorded._

---

## Next Immediate Steps (Phase 5)

1. Roster History — `Rosters` table in SQLite, week selector in Tab 3, ability to save/load a generated roster.
2. PDF/CSV export of the finalized roster.
3. Break-time informational warnings (15 min after 4.5 hrs, 30 min after 6 hrs) to post-gen checks in `logic.py`.
4. Update `docs/ARCHITECTURE.md` to reflect the weekly overrides schema (dias_folga, dias_ferias, dias_treinamento) in `config_semana`.

---

## Session Workflow Rules

- **STARTUP**: Read this file first before any code change.
- **WRAP-UP**: Update *Modified Files*, *Blockers*, and *Next Immediate Steps* before closing the session.
