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
| `logic.py` | Replaced `gerar_escala_automatica` with Codex algorithm; returns `(DataFrame, list[str])`; added clopening, keyholder, and hour-limit checks; added `import pandas as pd` |
| `app.py` | Unpacks new tuple return; stores `constraints_warnings` in session state; renders `⚠️ Avisos de Regras Trabalhistas` expander after roster; reset button clears warnings |
| `docs/CURRENT_STATE.md` | This file |
| `docs/CHANGELOG.md` | New Phase 4 entry appended |
| `.gitignore` | Created (excludes `*.db`, `__pycache__/`, `.env`, `.maestri/`) |

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

## Next Immediate Steps (Phase 4 — continued)

1. Encode Irish Working Time Act (WTI) rules as a standalone `validar_wti(employee, day, shift, week_log)` function in `logic.py` (max 48 hrs/week, 11 hrs rest between shifts, 15/30 min break thresholds).
2. Wire `validar_wti` into the new scheduler's candidate-filtering step so violations are blocked at assignment time, not just flagged after.
3. Extend the `⚠️ Avisos de Regras Trabalhistas` expander to also surface WTI violations from the post-generation check pass.

---

## Session Workflow Rules

- **STARTUP**: Read this file first before any code change.
- **WRAP-UP**: Update *Modified Files*, *Blockers*, and *Next Immediate Steps* before closing the session.
