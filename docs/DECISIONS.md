# DECISIONS — Escala (append-only)

> **Regra:** nunca editar linhas antigas. Uma decisão nova que muda outra ganha linha nova e diz "substitui D-xxx".
> Se outro documento (CURRENT_STATE, roles, memória, GTM) discordar daqui, vale a linha mais recente desta tabela.

| ID | Data | Decisão | Motivo | Quem aprovou |
|---|---|---|---|---|
| D-001 | 2026-11-09 | Stack mantida: Python + Streamlit, Supabase PostgreSQL (`roster-cafe`), Stripe, deploy no Streamlit Cloud. Migração para Next.js é decisão futura e separada. | Status quo em produção e funcionando; solver CP-SAT (ortools) em Python | Fernando (registro do status quo) |
| D-002 | 2026-11-09 | Maestro = Claude Code. Workers: Codex (algoritmo e lógica) e Grok (CMO / growth). Quem revisa nunca é quem fez. | Configuração verificada no canvas Maestri do Escala | Fernando |
| D-003 | 2026-11-09 | Preço oficial: €19 / €39 / €65 por mês (Starter / Standard / Plus). Substitui as menções a €20/mês e €19,90 em docs e roles antigos. Duração do trial AINDA NÃO decidida (conflito 15 vs 7 dias — pendente do Fernando). | Havia preços contraditórios entre roles, memória e CURRENT_STATE | Fernando, 2026-11-09 |
| D-004 | 2026-11-09 | Landing em Cloudflare Worker, domínio `escala.madfrog.ie` (repo `escala-landing`). | Já publicada e funcionando | Fernando (registro do status quo) |
| D-005 | 2026-11-09 | O Escala segue o padrão Mad Frog (`C:\MadFrog\hq\PADRAO_NOVO_SAAS.md`) por acréscimo: nenhuma pasta ou ficheiro existente renomeado. | Não quebrar os agentes que já leem os caminhos atuais | Fernando |