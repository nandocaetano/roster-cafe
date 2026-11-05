Wrap up the session: update the Second Brain docs and commit all changes.

Steps:
1. Run `git status` and `git diff` to identify every modified and untracked file changed this session.
2. Update `docs/CURRENT_STATE.md`:
   - Replace the **Modified Files** table with the files changed this session and a one-line description of each change.
   - Clear resolved blockers; record any new ones under **Blockers**.
   - Update **Next Immediate Steps** to reflect what comes next (not what was just done).
3. Append a new dated entry to `docs/CHANGELOG.md` following the existing format:
   - Date heading: `## YYYY-MM-DD — <Phase Name>: <Short Title>`
   - `### Added` / `### Changed` / `### Fixed` sections as appropriate.
   - `### Files Modified` listing every file touched.
4. Stage all relevant files. Do not stage secrets, `.env` files, or binary build artefacts.
5. Create a git commit using Conventional Commit format:
   - `feat:` for new features, `refactor:` for structural changes, `fix:` for bug fixes, `docs:` for documentation-only changes.
   - Subject line ≤ 72 characters.
   - Body: 2–3 bullet points describing *why* the changes were made, not just what changed.
6. Print exactly: "Session closed, docs updated, and git commit complete."
