Wrap up the current session by updating the Second Brain and committing all changes.

Steps:
1. Run `git status` and `git diff --stat` to identify every modified file this session.
2. Update `docs/CURRENT_STATE.md`:
   - Set Active Phase to reflect what is actually in progress now.
   - Replace the Modified Files table with files changed this session + one-line description.
   - Clear resolved blockers; add any new ones.
   - Update Next Immediate Steps to reflect what comes next (not what was just done).
3. Append a new dated entry to `docs/CHANGELOG.md` following the existing format:
   - Heading: `## YYYY-MM-DD — Phase N: Short Title`
   - `### Added` / `### Changed` / `### Fixed` sections as appropriate.
   - `### Files Modified` listing every file touched.
4. If `docs/ROADMAP.md` needs updating (a phase was completed or a new one started), update it now.
5. Stage all relevant files. Never stage `.env`, `*.db`, or binary build artefacts.
6. Create a git commit using Conventional Commit format (feat/fix/refactor/docs) with a subject ≤ 72 chars and a 2–3 bullet body explaining *why*.
7. End the commit message with:
   `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`
8. Print exactly: "Session closed, docs updated, and git commit complete."
