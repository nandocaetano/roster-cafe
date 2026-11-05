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
| `app.py` | PDF+Excel export expander (3 buttons: CSV/Excel/PDF); warning categorization by severity (error/warning/info); Tab 4 Analytics (4 metrics + 2 bar charts); `gerar_pdf_escala` import; `io` import; `_last_semana_label` saved to session_state |
| `logic.py` | `gerar_pdf_escala(roster_df, cafe_nome, semana_label) -> bytes` added — landscape A4 PDF with header, alternating row shading, Latin-1 encoding for Portuguese text |

---

## Current Architecture Snapshot

```
app_escala/
├── app.py          # Streamlit UI only — tabs 1/2/3/4 + auth gate + sidebar
├── database.py     # SQLite CRUD — Cafes, Users, Funcionarios, Rosters
├── logic.py        # Pure Python — shift math, availability checks, auto-scheduler, PDF export
├── roster_cafe.db  # SQLite database (created at runtime)
└── docs/           # This Second Brain
```

---

## Blockers

_None currently recorded._

---

## Next Immediate Steps

1. Update `docs/ARCHITECTURE.md` to reflect the weekly overrides schema and Rosters table.
2. User testing: generate a real roster with employees configured in Tab 2 (Folga, Treinamento) and verify PDF/Excel downloads render correctly.
3. Phase 6 planning: multi-week view / roster comparison across saved rosters.

---

## Session Workflow Rules

- **STARTUP**: Read this file first before any code change.
- **WRAP-UP**: Update *Modified Files*, *Blockers*, and *Next Immediate Steps* before closing the session.
