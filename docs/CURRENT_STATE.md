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
| `app.py` | Break-time conflict validation in Tab 2 submit; Exportar CSV button in Tab 3; Histórico de Escalas UI (save/load/delete) in Tab 3; `json` + roster CRUD imports added |
| `database.py` | `Rosters` table added to `init_db`; `salvar_roster`, `get_rosters`, `get_roster_by_id`, `deletar_roster` added |
| `logic.py` | Break-time warnings: >6h → 30 min obrigatória (WTI), >4.5h → 15 min recomendada |

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

## Next Immediate Steps

1. Update `docs/ARCHITECTURE.md` to reflect the weekly overrides schema and Rosters table.
2. PDF export (formatted, printable) — requires `reportlab` or `fpdf2` dep.
3. User-facing UX polish: break-time warning badge distinct from WTI errors in Tab 3 expander.
4. Begin Phase 6 planning: multi-week view / roster analytics dashboard.

---

## Session Workflow Rules

- **STARTUP**: Read this file first before any code change.
- **WRAP-UP**: Update *Modified Files*, *Blockers*, and *Next Immediate Steps* before closing the session.
