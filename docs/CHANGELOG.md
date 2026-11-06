# Changelog

---

## 2026-11-06 — Tooling: REA Methodology + Clean Room Design Protocol

### Added
- `.claude/commands/rea-analyze.md`: Custom slash command activating Reverse Engineering Architecture (REA) mode — decomposes competitor features into Core Problem / Logical Mechanism / UX Flow, then produces an original build plan for our Streamlit/OR-Tools stack with a Clean Room Checkpoint.
- `docs/CLEAN_ROOM_RULES.md`: Project-level Clean Room protocol — three rules governing how competitor features are studied and re-implemented (Deconstruction Only, Abstract Translation, Original Execution).

### Changed
- `.claude/commands/maestro-start.md`: Added Clean Room protocol acknowledgement to the boot summary output.

### Files Modified
- `.claude/commands/rea-analyze.md` (new)
- `.claude/commands/maestro-start.md`
- `docs/CLEAN_ROOM_RULES.md` (new)
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`

---

## 2026-11-06 — Phase 8: Billing Logic + GTM Strategy + Subscriptions Table

### Added
- `billing_logic.py` (CODEX): `get_subscription()`, `is_pro()`, `get_employee_limit()`, `check_feature_gate()`, `create_stripe_checkout_session()` — full Phase 8 billing layer; dual-backend psycopg2/sqlite; Stripe Checkout €20/mês inline price_data
- `docs/GTM_STRATEGY.md` (GROK): Full Dublin GTM — acquisition channels (Google Maps, Instagram DMs, walk-ins, RAI, LinkedIn), landing page copy (headline + 3 bullets + CTA), cold email script, WTI vs Excel sales argument + objection table, month-1 metrics funnel, 14-day execution playbook
- `requirements.txt`: `stripe>=7.0.0`
- **Supabase DB**: `Subscriptions` table created (tenant_id FK, plano, validade, stripe_customer_id, stripe_subscription_id, criado_em); seed row tenant_id=1 plano='free'

### Decision log
- Learned correct Maestri agent dispatch mechanics: `maestri list` → `maestri ask --batch` to ALL agents simultaneously; never give user prompts to copy manually
- Always confirm Codex file write approvals immediately with `maestri ask "Codex" "a"`
- Subscriptions table must run as 2 separate queries in Supabase SQL Editor (CREATE TABLE then INSERT) due to PostgreSQL planning order

### Files Modified
- `billing_logic.py` (new)
- `requirements.txt`
- `docs/GTM_STRATEGY.md` (new)
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`

---

## 2026-11-06 — Feat: Password Reset UI + Architecture Docs + Phase 8 Scope

### Added
- `database.py`: `get_all_users()` — returns all Users joined with Cafes.name, ordered by cafe then email; superadmin use only
- `database.py`: `reset_password(email, new_password)` — updates password_hash for any user by email; returns bool
- `app.py`: "🔑 Reset de Password" expander in superadmin sidebar — user selectbox (email + cafe), new password + confirm inputs, 6-char minimum validation, `rp_k` form-reset counter
- `.env.example`: Documents `DATABASE_URL` env var for local dev setup (`.env` already in `.gitignore`)

### Changed
- `docs/ARCHITECTURE.md`: Full rewrite — dual-backend strategy table, all 4 DB table schemas (Cafes, Users, Funcionarios, Rosters), CP-SAT solver diagram with C1–C7 constraints, password reset flow, updated session state keys (11 keys), deployment section
- `docs/ROADMAP.md`: Phase 8 scope clarified — Stripe Checkout + Subscriptions table + feature gating confirmed; License Keys and Stock/Clock-in add-ons explicitly deferred to future phases

### Decision log
- Pricing confirmed: €39.90 setup + €20/mês
- Phase 8 scope narrowed to Stripe only (no premature add-ons)
- GROK GTM prompt deferred until after this session's code ships; pricing now confirmed
- CODEX billing_logic.py deferred — existing `EMPLOYEE_LIMIT` already enforces the 20-employee cap; Stripe schema not yet defined

### Files Modified
- `app.py`
- `database.py`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `.env.example` (new)

---

## 2026-11-06 — Fix: Warning UI Flood & Qua Duplicate Slot

### Fixed
- `logic.py`: WTI break warnings collapsed from 1 line per shift (30+ total) into 2 summary lines: one for >6h shifts (mandatory 30-min break) and one for >4.5h–6h shifts (recommended 15-min break)
- `logic.py`: Floating point false positive `39.00h > 39.00h` — tolerance changed from `1e-9` to `0.05h` (3 min), so solver assignments at exactly the contract maximum no longer fire the "limite excedido" warning
- `app.py`: Duplicate `07:00 - 14:00` slot in Quarta-feira `turnos_padrao` replaced with `08:00 - 16:00` (matching all other weekdays)
- `app.py`: CP-SAT solver status line moved out of the warnings expander and displayed as a standalone `st.info()` banner

### Changed
- `app.py`: Unused `import json` removed

### Files Modified
- `app.py`
- `logic.py`

---

## 2026-11-06 — Feat: OR-Tools CP-SAT Solver

### Added
- `logic.py`: Full rewrite of `gerar_escala_automatica` using Google OR-Tools CP-SAT solver
  - Boolean variable matrix `x[e, d, s]` and `unassigned[d, s]` for every employee/day/shift triple
  - Hard constraints: coverage (C1), availability (C2), 1 shift/day (C3), max contract hours in minutes (C4), keyholder on closing (C5), WTI clopening 11h rest (C6), novato max 1 per opening/closing block per day (C7)
  - Objective: `BIG_PENALTY(100k) × unassigned + Σ(over + under)` per employee vs target hours
  - Solver time limit: 10 seconds (`max_time_in_seconds`)
  - Returns `(pd.DataFrame, list[str])` — signature unchanged, drop-in replacement
- `requirements.txt`: `ortools>=9.8.0`
- 8 demo employees inserted into Supabase tenant_id=1 for UI testing (Cristina, Franco, Maria, João, Sara, Liam, Pedro, Natalie)

### Files Modified
- `logic.py`
- `requirements.txt`

---

## 2026-11-06 — Perf: DB Caching & Session Guard

### Changed
- `app.py`: `init_db()` now runs once per browser session (guarded by `session_state['db_initialized']`), not on every Streamlit rerun — saves 1–2 s on Supabase (6+ round-trip DDL statements eliminated per click)
- `app.py`: Added `@st.cache_data` wrappers `_cached_cafe(ttl=300)`, `_cached_funcionarios(ttl=60)`, `_cached_rosters(ttl=30)` — avoids new psycopg2 connections on every rerender
- `app.py`: `equipe_v` and `roster_v` version counters in `session_state` incremented after every write (add/edit/desativar/salvar/deletar) to bust cache without stale data

### Files Modified
- `app.py`

---

## 2026-11-05 — Phase 7: Supabase/PostgreSQL Migration

### Added
- `database.py`: Full dual-backend rewrite — `_PG = bool(os.environ.get('DATABASE_URL'))` flag; `_P = '%s' if _PG else '?'` placeholder; `_get_conn()` returns psycopg2 (RealDictCursor) or sqlite3 based on flag
- `database.py`: Separate CREATE TABLE SQL blocks for PG (SERIAL, NOW()::TEXT, BOOLEAN DEFAULT TRUE) vs SQLite (AUTOINCREMENT, datetime('now'), BOOLEAN DEFAULT 1)
- `database.py`: PG safe migrations via `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`; SQLite migrations via try/except OperationalError
- `database.py`: `RETURNING id` for PG INSERTs; `cursor.lastrowid` for SQLite — both return new row id
- `requirements.txt`: `psycopg2-binary>=2.9.0`

### Changed
- Supabase project created; Transaction pooler URL (IPv4, Frankfurt) set as `DATABASE_URL` in Streamlit Cloud Secrets
- App confirmed live and authenticated at Streamlit Cloud

### Files Modified
- `database.py`
- `requirements.txt`

---

## 2026-11-05 — Phase 7 Prep + Algorithm Rewrite + UX Fixes

### Added
- `database.py`: `nivel TEXT DEFAULT 'experiente'` column on Funcionarios (PG: `ADD COLUMN IF NOT EXISTS`; SQLite: try/except)
- `database.py`: `adicionar_funcionario` / `atualizar_funcionario` accept `nivel` param
- `app.py` Tab 1: `nivel` selectbox (experiente/novato) in Novo Funcionário and Editar forms; `nivel` column shown in employee table
- `app.py` Tab 2: `"nivel"` passed through to `config_semana` per employee
- `logic.py`: Novato constraint — max 1 novato per opening block and per closing block per day (`novato_opening_today` / `novato_closing_today` flags)
- `logic.py`: `closing_count` dict tracks closing shifts per employee across the week
- `logic.py`: `_remaining_avail_days(employee, from_day_index)` helper counts future available days
- `logic.py`: 4-key urgency sort — restricted availability first → closing_count balance → urgency ratio (hours_needed / remaining_days) → minimum hours deficit
- `logic.py`: 08:00-16:00 auto-drop when available staff count < number of shifts for the day
- `app.py` sidebar: `nc_k` counter resets "Registrar Novo Cafe" form fields after successful submission
- `app.py` Tab 1: "Até" time defaults to 18:15 in Específico availability selector

### Files Modified
- `app.py`
- `database.py`
- `logic.py`

---

## 2026-11-05 — Phase 6: RBAC, Commercial Limits & Ajuda Tab

### Added
- `database.py`: `role` column on Users; `superadmin` role seeded for `admin@cafe.com`; migration upgrades existing admin seed to superadmin
- `database.py`: `EMPLOYEE_LIMIT = 20`; `adicionar_funcionario` raises `ValueError("limite_funcionarios:20")` when limit reached
- `app.py`: Auth gate — only `superadmin` role sees "Registrar Novo Cafe" expander in sidebar
- `app.py` Tab 1: Catches `limite_funcionarios` ValueError and shows user-friendly error message
- `app.py` Tab 5 (Ajuda): Full help tab with onboarding guide, availability table, scheduler rules, WTI rules, and FAQ

### Changed
- `app.py` login UI: Gradient card (purple/indigo) with styled form; Register tab removed — user creation is superadmin-only via sidebar
- `database.py`: Seed migration step upgrades role 'admin' → 'superadmin' for admin@cafe.com on every `init_db()` (idempotent)

### Files Modified
- `app.py`
- `database.py`

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
