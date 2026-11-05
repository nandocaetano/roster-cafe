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
| `app.py` | `render_availability_selector` opcoes updated to include "Folga" and "Férias"; index defaults replaced with `opcoes.index(...)` calls to avoid hardcoded offsets |
| `logic.py` | `available()` treats "Folga"/"Férias" as unavailable; WTI 11-hr rest enforced in candidate filter via `prev_day_last_end` tracking; 7-consecutive-day warning added to post-gen checks |

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

1. Surface WTI violations in Tab 3 `⚠️ Avisos de Regras Trabalhistas` expander — WTI warnings are now generated but need a distinct `st.warning` badge vs labour-rule errors.
2. Add break-time informational warnings (15 min after 4.5 hrs, 30 min after 6 hrs) to post-gen checks in `logic.py`.
3. Update `docs/ARCHITECTURE.md` to reflect new availability values (Folga, Férias) in the Funcionarios table description.
4. Begin Phase 5 planning: Roster History — `Rosters` table, week selector, PDF/CSV export.

---

## Session Workflow Rules

- **STARTUP**: Read this file first before any code change.
- **WRAP-UP**: Update *Modified Files*, *Blockers*, and *Next Immediate Steps* before closing the session.
