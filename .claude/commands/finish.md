Wrap up the session: update the Second Brain docs and prepare the suggested commit.

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
4. Liste os arquivos que devem entrar no commit (nunca .env, *.db, segredos ou binários de build) e mostre o comando git add exato. Não rode.
5. Mostre a mensagem de commit sugerida (Conventional Commit) e o comando git exato. Não rode. O Nando roda um comando por vez.
6. Print exactly: "Session closed, docs updated. Suggested git commit ready for Nando."
