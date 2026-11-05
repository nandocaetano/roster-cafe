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
| `app.py` | Edit form refactored — removed `st.form` wrapper, added employee-specific widget keys so "Específico" availability field triggers immediately on selectbox change; sidebar cafe registration expander added; `clear_on_submit=True` on new employee form; "Fecho"→"Fechamento" in turnos and str.contains filter; `render_availability_selector` gains `placeholder` and `help` on time input |
| `logic.py` | "Fecho"→"Fechamento" in `calcular_horas_turno` docstring and `pode_trabalhar` check |

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
4. Consider applying same edit-form pattern (outside `st.form`) to the "Novo Funcionário" form so "Específico" also triggers immediately there.

---

## Session Workflow Rules

- **STARTUP**: Read this file first before any code change.
- **WRAP-UP**: Update *Modified Files*, *Blockers*, and *Next Immediate Steps* before closing the session.
