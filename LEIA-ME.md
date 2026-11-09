# Escala (Coffee Shop Roster) — LEIA-ME

> Padrão Mad Frog Studios: `C:\MadFrog\hq\PADRAO_NOVO_SAAS.md`. Adequação Fase A em 2026-11-09 (Europe/Dublin).
> **Nada existente foi renomeado ou movido.** Só foram acrescentados ficheiros.

## Ordem de leitura (todo agente, toda sessão)

1. `docs/CURRENT_STATE.md` — fonte única da verdade (inalterada; faz o papel do STATUS do padrão)
2. `docs/DECISIONS.md` — decisões append-only (preço oficial: D-003)
3. `docs/SESSION_HANDOFF.md` — onde a última sessão parou
4. `docs/AGENTS.md` — quem é quem, canal `maestri ask`, o que exige aprovação do Fernando
5. `cerebro/COFRE.md` — índice de segredos (só nomes e onde vivem; nunca valores)
6. Depois, conforme a tarefa: `docs/ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/RULES.md`, `docs/CLEAN_ROOM_RULES.md`, `PRODUCT.md`

## Equivalências com o padrão (sem renomear)

| Padrão Mad Frog | No Escala |
|---|---|
| `docs/STATUS.md` | `docs/CURRENT_STATE.md` |
| skills start / save / finish | `.claude/commands/maestro-start.md`, `maestro-save.md`, `finish.md` |
| `docs/BUSINESS.md` | `docs/GTM_PLAN.md` + `docs/GTM_STRATEGY.md` |
| `skills/` | `skills/` (prompts de marketing) + `.claude/skills` e `.agents/skills` (design) |
| `.maestri/roles` | `.maestri/roles/<uuid>` (não mexer nas pastas; nomes só pelo Maestri UI) |
| `journal/` | `journal/` (novo) |

## Regras rápidas

- Se dois documentos discordarem, vale o `docs/DECISIONS.md` (linha mais recente).
- Nunca escrever senhas, chaves ou connection strings em docs, notas, prompts ou commits.
- Push, deploy, Stripe live, pagamentos, contato com clientes, gastos, instalações e exclusões: só com aprovação do Fernando.
- Mudança de pasta planejada: ver `MIGRATION.md`.