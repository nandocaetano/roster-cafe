# SESSION HANDOFF — Escala

> Nova entrada no topo a cada sessão. Não apagar entradas antigas.

## Modelo

- **Data:** AAAA-MM-DD (Europe/Dublin)
- **Quem:** (agente / pessoa)
- **O que foi feito:**
- **Próximo passo:**
- **Bloqueios:**

---

## 2026-11-10 — Protótipo UX aprovado + commits dev + permissões

- **Quem:** Maestro (Claude Code) + Fernando
- **O que foi feito:**
  - Commits no branch `dev` (sem push):
    - `0592eba` — security: RLS habilitado nas 5 tabelas restantes
    - `22563af` — chore: limpeza das skills do mattpocock (37 removidas, 4 mantidas)
    - `da0f148` — docs: D-010 e D-011 registrados; CURRENT_STATE e SESSION_HANDOFF atualizados
  - `settings.local.json` reduzido: `permissions.allow` agora só com `git status`, `git diff`, `git log`, `git show` (removidos `npx wrangler` e `npm run`).
  - Protótipo UX (D-011) publicado como Artifact e aprovado pelo Fernando. Acabamento aprovado para implementação:
    - Conteúdo centralizado `max-width: 1160px`; cards do fluxo guiado com `max-width: 560px` centrados.
    - `+ Add another` e `+ Add another shift` com borda tracejada e cor da marca (`.btn-dashed`).
    - Morning e Afternoon com badges de violeta diferentes (`.sp-m` / `.sp-a`); "Off" em cinza legível (`.td-off`).
    - "Regenerate" abre modal de confirmação antes de sobrescrever.
    - Mobile: barra de passos só com números + Skip abaixo da barra; sem scroll horizontal na página; tabela da Rota em `overflow-x: auto`.
- **Próximo passo:** Aguardar OK da Nati no protótipo → implementar D-011 no `app.py` no branch `dev` → testar → pedir aprovação para push `dev → main`.
- **Bloqueios:**
  - Aprovação da Nati no protótipo pendente.
  - `skills-lock.json` não commitado — decidir se incluir em commit futuro.
  - Verificar origem dos hooks do Impeccable no `settings.local.json` (foram mantidos sem revisão).
  - `madfrog.ie` NXDOMAIN — bloqueador externo (Register365/IEDR), sem ação técnica.
  - Stripe live mode e credentials rotation — HITL, requerem aprovação explícita.

---

## 2026-11-09 — RLS habilitado + skills cleanup

- **Quem:** Maestro (Claude Code)
- **O que foi feito:**
  - Skills do mattpocock: 37 movidas para `.skills-backup/` em cada pasta; mantidas apenas `grill-me`, `to-spec`, `to-tickets` em `.claude/skills/` e `.agents/skills/`. `.skills-backup/` adicionado ao `.gitignore`.
  - RLS habilitado nas 5 tabelas faltantes (`cafes`, `users`, `funcionarios`, `rosters`, `subscriptions`) via `supabase db query --remote`. Total: 9/9 tabelas com `rowsecurity = true`.
  - SQL versionado em `supabase/rls_enable.sql` e `supabase/rls_rollback.sql`.
  - Smoke tests 4/4 passando (imports + billing_logic).
- **Próximo passo:**
  - Teste manual obrigatório (confirmação do usuário): login → gerar escala → criar funcionário → checkout de teste da landing.
  - Após confirmação: Stripe live mode (HITL) + credentials rotation (HITL).
- **Bloqueios:**
  - Teste E2E manual (login, escala, funcionário, checkout) pendente — requer browser do usuário.
  - `madfrog.ie` NXDOMAIN — bloqueador externo (Register365/IEDR), sem ação técnica.
  - Stripe live mode — HITL, requer aprovação explícita.
  - Credentials rotation — HITL, requer aprovação explícita.

---

## 2026-11-09 — Push dos dois repos + fix Python 3.14

- **Quem:** Maestro (Claude Code)
- **O que foi feito:**
  - Confirmado: Streamlit Cloud publica a partir da branch `main` (visto nas settings)
  - Push de 8 commits para `app_escala/main` e 2 commits para `escala-landing/main`
  - Detectado ImportError no Streamlit após rebuild: Python 3.14 não suporta wheels de `ortools`/`psycopg2-binary`
  - Corrigido: adicionado `runtime.txt` com `python-3.11` → pushado → rebuild em curso
  - Cloudflare Worker (`escala.madfrog.ie`): push ao GitHub NÃO faz deploy automático; código atualizado no git mas Worker ainda serve versão anterior; deploy manual (`npm run deploy`) requer aprovação do Fernando
  - Resend DNS: ainda a propagar (status "Checking DNS" no Resend dashboard; `madfrog.ie` retorna NXDOMAIN)
- **Próximo passo:** decidir deploy do Worker (`npm run deploy` em `escala-landing`) + confirmar login manualmente com credenciais reais
- **Bloqueios:**
  - ✅ App online: ecrã de login confirma deploy bem-sucedido com Python 3.11
  - Resend DNS: aguardando propagação IEDR do `madfrog.ie` → Cloudflare
  - Worker deploy: `escala.madfrog.ie` desatualizado (modal checkout com nome do café não está live); requer `npm run deploy` + aprovação Fernando
  - Duração do trial (15 vs 7 dias) — D-003 ainda pendente
  - Stripe live mode — HITL, requer aprovação Fernando
  - Credentials rotation — HITL, requer aprovação Fernando

---

## 2026-11-09 — Adequação Fase A (padrão Mad Frog)

- **Quem:** Gerente de Criação (Cérebro), com aprovação do Fernando
- **O que foi feito:** criados LEIA-ME, README, MIGRATION, docs/DECISIONS, docs/SESSION_HANDOFF, docs/AGENTS, cerebro/COFRE, journal/. Uma linha no topo do CURRENT_STATE. 4 entradas no .gitignore. Nada movido, renomeado, apagado ou commitado.
- **Próximo passo:** Fernando revê e decide o commit; depois Fase B (mudança para `C:\MadFrog\projetos\escala\app`, ver MIGRATION.md).
- **Pendências / bloqueios:**
  - 7 commits locais na `main` ainda não enviados ao GitHub (push = aprovação do Fernando)
  - Dúvida de deploy: o Streamlit Cloud publica a partir da `main` ou da `master`? (`master` está 11 commits atrás)
  - Landing: `src/pages/index.astro` com alterações sem commit
  - Duração do trial (15 vs 7 dias) — ver D-003
  - Corrigir nomes dos roles no Maestri UI (o role "Senior Full-Stack Enginee" é na verdade o Maestro)
  - Criar 4 notas no canvas Maestri: LEIA-ME, STATUS, DECISIONS (trancada), SESSION_HANDOFF
  - Credencial em texto puro na memória do Claude: Fernando copia para o Bitwarden e depois troca por referência
  - Fase B: mudança de pasta com o Maestri fechado