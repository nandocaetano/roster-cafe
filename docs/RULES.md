# Development Rules

Constraints that must be respected in every session and every pull request.

---

## Session Workflow

### STARTUP
Before writing a single line of code:
1. Read `docs/CURRENT_STATE.md` — confirm active phase, blockers, and next steps.
2. Read the relevant section of `docs/ARCHITECTURE.md` if touching DB schema or data flow.
3. Never assume the state from a previous conversation — always verify against the docs.

### WRAP-UP
After completing any feature or phase:
1. Update `docs/CURRENT_STATE.md`:
   - **Modified Files** — list every file changed and what changed.
   - **Blockers** — anything that could not be completed and why.
   - **Next Immediate Steps** — the first 2–3 concrete tasks for the next session.
2. Add an entry to `docs/CHANGELOG.md`.
3. If a phase is completed, update `docs/ROADMAP.md` status.

---

## Multi-Tenancy Isolation

- **Every** DB query that reads or writes `Funcionarios` must include `AND tenant_id = ?`.
- UPDATE and DELETE statements must include `WHERE ... AND tenant_id = ?` as a cross-tenant write guard.
- `tenant_id` is always sourced from `st.session_state['tenant_id']`, which is set by the auth system — never hardcoded in UI logic.
- Never pass `tenant_id = 1` as a fallback inside `app.py`; that shortcut bypasses isolation.

---

## Streamlit State Guidelines

- All cross-tab state lives in `st.session_state` with explicit string keys.
- Defined session state keys and their owners:

  | Key | Owner | Description |
  |---|---|---|
  | `user` | auth gate | Authenticated user dict |
  | `tenant_id` | auth gate | Active tenant id |
  | `config_semana` | Tab 2 form | Weekly hours/availability snapshot |
  | `roster_df` | Tab 3 buttons | Current roster DataFrame |

- Never store mutable objects (DataFrames, connections) directly in session state without understanding rerun implications.
- `st.rerun()` triggers a full script re-execution — any state not in `st.session_state` will be lost.

---

## Security Requirements

- Passwords are stored exclusively as `salt_hex:sha256_hex` via `_hash_password` in `database.py`. Plaintext passwords never touch the DB.
- The `_hash_password` and `_check_password` functions are private (underscore-prefixed) — do not call them from `app.py`.
- When upgrading to `bcrypt` or `argon2`, only `database.py` changes — the interface (`create_user`, `verify_credentials`) stays the same.
- Do not log or display password values anywhere in the UI or console.
- Do not add debug endpoints or admin backdoors that bypass `verify_credentials`.

---

## Module Boundaries

| Module | Allowed imports | Forbidden imports |
|---|---|---|
| `logic.py` | `re`, `datetime` (stdlib only) | `streamlit`, `sqlite3`, `database` |
| `database.py` | `sqlite3`, `pandas`, `hashlib`, `os`, `datetime` | `streamlit`, `logic` |
| `app.py` | `streamlit`, `pandas`, `database`, `logic` | `sqlite3` directly |

Keeping `logic.py` free of I/O dependencies makes it unit-testable in isolation.

---

## Feature Constraints

- **Do not remove or alter** the Availability Tree (Tab 1), the Dynamic Hours Panel (Tab 3), or the Keyholder closing-shift check (Tab 3). These are core business features.
- The `turnos_padrao` dictionary in `app.py` Tab 3 is the canonical shift template — changes there affect the auto-scheduler directly.
- Budget thresholds (290 / 300 / 305 hours) in Tab 2 are business rules — do not change them without product approval.

---

## Code Style

- No comments that explain *what* the code does — only *why* when non-obvious.
- No multi-paragraph docstrings — one short line maximum.
- No backwards-compatibility shims for removed code.
- No feature flags.
- Three similar lines before considering an abstraction.
