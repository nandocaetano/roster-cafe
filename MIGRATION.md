# MIGRATION — adequação ao padrão Mad Frog

## 2026-11-09 — Fase A (só acréscimos) — feito

Aprovado pelo Fernando. Nada movido, renomeado ou apagado. Nada commitado.

Criados: `LEIA-ME.md`, `README.md`, `MIGRATION.md`, `docs/DECISIONS.md`, `docs/SESSION_HANDOFF.md`, `docs/AGENTS.md`, `cerebro/COFRE.md`, `journal/README.md`.
Alterados: `docs/CURRENT_STATE.md` (1 linha no topo), `.gitignore` (4 entradas no fim).
Backups dos originais: `C:\MadFrog\arquivo\escala_backups_20261109\`.

## Fase B — mudança de pasta (planejada, NÃO feita)

Destino: `C:\MadFrog\projetos\escala\app` (e a landing em `C:\MadFrog\projetos\escala\landing`).
Só com o Fernando presente, Maestri/Claude/Codex/Grok/Streamlit fechados e tudo commitado.

### Checklist de referências ao caminho antigo `C:\Users\caeta\Desktop\app_escala`

- [ ] `~\.maestri\workspaces\8bcee186-01a5-4025-b698-bbd85e690fd5\workspace.json` — 3× `workingDirectory` (workspace, terminal "Grok - CMO & Growth Hacker", terminal "powershell") — preferir mudar pelo Maestri UI; há backups em `~\.maestri\backups`
- [ ] Nota Maestri "Guia Deploy & Live" — 2 caminhos (`app_escala` e `escala-landing`)
- [ ] `.maestri\roles\*\AGENTS.md` e `CLAUDE.md` — 6 blocos `<working_directory>` (3 roles)
- [ ] `.maestri\roles\e9edd300-ab05-43ac-b83e-e0983a10fea1\.claude\settings.local.json` — `Read(//c/Users/caeta/Desktop/escala-landing/**)`
- [ ] `.claude\commands\auto-sync.md` — caminho da memória do Claude
- [ ] `.claude\commands\grill-docs.md` — caminho da memória do Claude
- [ ] `~\.claude\projects\` — DUPLICAR (não apagar) 2 pastas para o novo nome:
  - `C--Users-caeta-Desktop-app-escala` (memória) → `C--MadFrog-projetos-escala-app`
  - `C--Users-caeta-Desktop-app-escala--maestri-roles-e9edd300-ab05-43ac-b83e-e0983a10fea1` (sessões do Maestro) → `C--MadFrog-projetos-escala-app--maestri-roles-e9edd300-ab05-43ac-b83e-e0983a10fea1`
- [ ] `~\.claude.json` — entrada de projeto (confiança/permissões) para o caminho novo
- [ ] `~\.codex\config.toml` — `[projects.'c:\users\caeta\desktop\app_escala']` + `hooks.state` do `.codex\hooks.json`
- [ ] `~\.grok\trusted_folders.toml` — pasta confiável (e `active_sessions.json` com o cwd do role)
- [ ] Antigravity: nenhuma referência (o Escala não usa Antigravity)
- [ ] Depois: atualizar `C:\MadFrog\hq\PADRAO_NOVO_SAAS.md`, `MUDANCA_DE_ENDERECO.md`, `C:\MadFrog\hq\PORTFOLIO.md`
- [ ] Teste: `/maestro-start`, um `maestri ask` ao Grok e ao Codex, app em `localhost:8501`, `npm run build` na landing

Não dependem do caminho: GitHub, Supabase (`supabase\.temp` usa a ref), Stripe, Cloudflare, `wrangler.toml`, portal `localhost:8501`.