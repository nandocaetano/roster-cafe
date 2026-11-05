# Changelog

Chronological log of major updates. Most recent first.

---

## 2026-11-05 — Phase 4: UX Fixes & Edit Form Refactor

### Fixed
- `app.py` Edit form ("Editar ou Remover") refactored to remove `st.form` wrapper — availability selectbox changes now trigger immediate rerun so the "Específico" time input appears/disappears on selection without needing to submit
- Employee-specific widget keys (`ed_{nome}_*`) prevent state collision when switching between employees in the edit panel
- `form_submit_button` → regular `st.button` with explicit keys for Salvar and Desativar

### Changed
- `app.py` "Novo Funcionário" form: `clear_on_submit=False` → `True` so form clears after cadastro
- `app.py` `render_availability_selector`: added `placeholder="ex: 09:00 - 17:00"` and `help` text to the time `text_input`
- `app.py` sidebar: "➕ Registrar Novo Cafe" expander added to authenticated sidebar (previously only accessible from the login screen)
- `app.py` turnos_padrao and str.contains filter: "Fecho" → "Fechamento" across all 21 shift strings and the keyholder filter
- `logic.py` `calcular_horas_turno` docstring and `pode_trabalhar` check: "Fecho" → "Fechamento"

### Files Modified
- `app.py`
- `logic.py`
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`

---

## 2026-11-05 — Phase 4: Codex Scheduler Integration

### Changed
- `gerar_escala_automatica` in `logic.py` fully replaced with Codex algorithm
  - New signature: `(config_semana, turnos_padrao) -> (pd.DataFrame, list[str])`
  - Closing shifts now detected by end-time > 17:00 (not by keyword "Fecho")
  - Clopening guard: opening shifts block employees who closed the previous day
  - Post-generation checks: keyholder-on-closing, weekly hour limits (min/max), clopening cross-day validation
  - `numeric_value` helper resolves multiple field-name aliases (horas_alvo, horas_max, etc.)
- `app.py` Tab 3 updated to consume new return tuple
  - `constraints_warnings` stored in `st.session_state`
  - `⚠️ Avisos de Regras Trabalhistas` expander renders after roster; clopening/keyholder/hour violations shown as `st.error`, others as `st.warning`
  - Reset button now clears `constraints_warnings` alongside `roster_df`

### Added
- `import pandas as pd` at module level in `logic.py`
- `.gitignore` (excludes `*.db`, `__pycache__/`, `.env`, `.maestri/`)
- Git repository initialized at project root

### Files Modified
- `logic.py`
- `app.py`
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`
- `.gitignore` (new)

---

## 2026-11-05 — Phase 3: Authentication System

### Added
- `Users` table in SQLite: `id`, `tenant_id`, `email`, `password_hash`, `role`, `created_at`
- `_hash_password(password)` — 16-byte random salt + SHA-256, stored as `salt_hex:hash_hex`
- `_check_password(password, stored)` — constant-time-safe reconstruction and comparison
- `create_user(tenant_id, email, password, role)` in `database.py`
- `verify_credentials(email, password)` in `database.py` — returns user dict or None
- `get_cafe_by_id(cafe_id)` in `database.py` — returns cafe dict for sidebar display
- Auth gate in `app.py`: Login and Register tabs; `st.stop()` blocks unauthenticated rendering
- Authenticated sidebar: cafe name, user email, role badge, Logout button
- Default seed: `admin@cafe.com` / `admin123` created on first `init_db()` run

### Changed
- `app.py` imports updated; old `tenant_id = 1` bootstrap replaced by auth gate
- `TENANT_ID` now sourced from `st.session_state['tenant_id']` set during login

### Files Modified
- `database.py`
- `app.py`

---

## 2026-11-05 — Phase 2: Multi-Tenancy

### Added
- `Cafes` table: `id`, `name`, `admin_email`, `created_at`
- `tenant_id` FK column on `Funcionarios` — added via safe `ALTER TABLE` migration
- `get_cafes()`, `criar_cafe(name, admin_email)` in `database.py`
- Default tenant seeded: `id=1, name="Default Cafe"` on first `init_db()`

### Changed
- All CRUD functions (`get_funcionarios_ativos`, `adicionar_funcionario`, `atualizar_funcionario`, `desativar_funcionario`) now require `tenant_id` as first parameter
- UPDATE/DELETE queries include `AND tenant_id = ?` cross-tenant write guard
- `app.py` bootstrapped `st.session_state['tenant_id'] = 1` as placeholder for future auth

### Files Modified
- `database.py`
- `app.py`

---

## 2026-11-05 — Phase 1: Modularisation

### Added
- `database.py` — all SQLite connection logic, table creation, and CRUD functions
- `logic.py` — pure business logic: `calcular_horas_turno`, `pode_trabalhar`, `gerar_escala_automatica`

### Changed
- `app.py` refactored to Streamlit UI only — imports from `database.py` and `logic.py`
- `pode_trabalhar` extracted from inline closure in Tab 3 button handler to standalone function in `logic.py`
- `gerar_escala_automatica` extracted to `logic.py` — now a testable, Streamlit-free function
- `render_availability_selector` retained in `app.py` (uses `st.*` widgets — not pure logic)

### Files Modified
- `app.py` (rewritten)
- `database.py` (new)
- `logic.py` (new)
