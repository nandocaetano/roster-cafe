Wrap up the current session by updating the Second Brain and prepare the suggested commit.

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
5. Liste os arquivos que devem entrar no commit (nunca .env, *.db, segredos ou binários de build) e mostre o comando git add exato. Não rode.
6. Mostre a mensagem de commit sugerida (Conventional Commit, feat/fix/refactor/docs, subject ≤ 72 chars, 2–3 bullet body) e o comando git exato com Co-Authored-By. Não rode. O Nando roda um comando por vez.
7. Print exactly: "Session closed, docs updated. Suggested git commit ready for Nando."
