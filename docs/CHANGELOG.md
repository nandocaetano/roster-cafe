# Changelog

---

## 2026-11-05 — Phase 5: PDF/Excel Export, Warning Severity & Analytics Tab

### Added
- `logic.py`: `gerar_pdf_escala(roster_df, cafe_nome, semana_label) -> bytes` — landscape A4 PDF with styled header, alternating day shading, Latin-1 encoding for Portuguese characters; uses `fpdf` 1.7.2
- `app.py` Tab 3: **⬇️ Exportar Escala** collapsible expander with 3 download buttons — 📄 CSV, 📊 Excel (`openpyxl`), 🖨️ PDF — replacing the single CSV button
- `app.py` Tab 3: Warning categorization — groups `constraints_warnings` into errors / warnings / infos; expander label shows counts; expander auto-expands when errors exist; uses `st.error` / `st.warning` / `st.info` per severity
- `app.py` Tab 4: **📊 Análise** tab with 4 KPI metrics (Total de Turnos, Preenchidos, Gaps, Cobertura %), Horas por Funcionário vs. Alvo bar chart, and Cobertura por Dia stacked bar chart

### Changed
- `app.py` Tab 3: 4-column action button row → clean 3-column row (Esqueleto Vazio, Gerar Automática, Resetar Aba); exports moved to dedicated expander
- `app.py` Tab 3: `_last_semana_label` now saved to `session_state` on roster save so PDF export can include the week label

### Files Modified
- `app.py`
- `logic.py`
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`

---

## 2026-11-05 — Phase 5: Break-time Warnings, Export CSV & Roster History

### Added
- `logic.py` post-gen: break-time warnings per assigned shift — >6h triggers WTI mandatory 30-min pause; >4.5h triggers recommended 15-min pause
- `app.py` Tab 2: conflict validation on form submit — warns if the same day is marked as both Folga (or Férias) and Treinamento; blocks save until resolved
- `app.py` Tab 3: **⬇️ Exportar CSV** button — enabled when a roster exists, disabled otherwise; downloads `escala.csv` via `st.download_button`
- `database.py`: `Rosters` table (`id, tenant_id, semana, dados_json, criado_em`) created in `init_db`
- `database.py`: `salvar_roster`, `get_rosters`, `get_roster_by_id`, `deletar_roster` CRUD functions
- `app.py` Tab 3: **💾 Histórico de Escalas** section — save current roster with a week label, list saved rosters, 📂 load or 🗑️ delete each entry

### Files Modified
- `app.py`
- `database.py`
- `logic.py`
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`

---

## 2026-11-05 — Phase 4: Weekly Overrides, Training Hours & Soft Hour Tolerance

### Added
- `app.py` Tab 2: global `margem_horas` number input (default 2h) — configures the per-employee soft tolerance band around `horas_alvo`
- `app.py` Tab 2: per-employee multiselects for 🏖️ Folga, ✈️ Férias, 📚 Treinamento days + `H. Treino` total hours input — stored in `config_semana` as `dias_folga`, `dias_ferias`, `dias_treinamento`, `horas_treinamento`
- `app.py` Tab 2: `horas_min` and `horas_max` from DB now passed through to `config_semana` so the scheduler enforces contract limits correctly
- `logic.py` `available()`: weekly override checks — returns False if the day is in `dias_folga`, `dias_ferias`, or `dias_treinamento`
- `logic.py` `gerar_escala_automatica`: training hours pre-loaded into `assigned_hours` before shift scheduling, counting against the weekly total
- `logic.py` `gerar_escala_automatica`: soft tolerance warnings — fires when total hours fall outside `[target − margem, target + margem]` without breaching the hard contract max/min
- `app.py` Tab 3 hours panel: training hours added to per-employee totals; margem used as threshold for red/blue/green status; label shows `± margem`

### Changed
- `app.py` `render_availability_selector`: "Folga" and "Férias" removed from Tab 1 options — these are now weekly-only via Tab 2; backward-compat maps legacy DB values to "Indisponível"
- `logic.py` `gerar_escala_automatica` signature: `margem_horas: float = 2.0` parameter added
- `app.py` Tab 3 auto button: passes `st.session_state['margem_horas']` (default 2.0) to `gerar_escala_automatica`

### Files Modified
- `app.py`
- `logic.py`
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`

Chronological log of major updates. Most recent first.

---

## 2026-11-05 — Phase 4: Folga/Férias + WTI Labour Constraints

### Added
- `app.py` `render_availability_selector`: "Folga" and "Férias" added to `opcoes` list; list reordered to `["Livre", "Só Manhã", "Só Tarde", "Indisponível", "Folga", "Férias", "Específico"]`; index defaults replaced with dynamic `opcoes.index()` calls to avoid brittle hardcoded offsets
- `logic.py` `available()`: "Folga" and "Férias" now treated as unavailable alongside "Indisponível"
- `logic.py` `gerar_escala_automatica`: WTI 11-hr rest rule enforced at candidate-filter time — tracks `prev_day_last_end` per employee across days; blocks assignments where gap to previous day's last shift end < 660 min
- `logic.py` post-gen check: warns if any employee is assigned all 7 days with no rest day (WTI minimum 1 day off per week)

### Files Modified
- `app.py`
- `logic.py`
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`

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
