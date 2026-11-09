# SESSION HANDOFF — Escala

> Nova entrada no topo a cada sessão. Não apagar entradas antigas.

## Modelo

- **Data:** AAAA-MM-DD (Europe/Dublin)
- **Quem:** (agente / pessoa)
- **O que foi feito:**
- **Próximo passo:**
- **Bloqueios:**

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