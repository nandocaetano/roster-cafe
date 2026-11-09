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
| D-006 | 2026-11-09 | Runtime fixo em Python 3.11 via `runtime.txt`. Nenhum push em `main` sem os smoke tests passarem (`python tests/test_smoke.py` + `python test_fairness_solver.py`). Sessões com push operam em modo manual (aprovação explícita do Fernando antes de cada push/deploy). | Push sem smoke test derrubou produção: Python 3.14 incompatível com ortools/psycopg2-binary wheels. | Fernando, 2026-11-09 |
| D-007 | 2026-11-09 | Stripe só vai para live mode no lançamento do primeiro cliente real. Checklist obrigatório: (1) teste E2E completo em modo teste; (2) chaves live nos Secrets (Streamlit + Supabase) e no Bitwarden; (3) preços e webhook recriados no dashboard Stripe live; (4) uma compra real pequena confirmada; (5) Termos de Serviço, Política de Privacidade e Política de Reembolso publicados em `escala.madfrog.ie`. | Proteger contra cobrança acidental de clientes reais com configuração incompleta. | Fernando, 2026-11-09 |
| D-008 | 2026-11-09 | Trial = 7 dias com cartão obrigatório. Substitui D-003 (conflito 15 vs 7 dias resolvido). Atualizado em `billing_logic.py`, `app.py`, Edge Function `create-checkout` e landing page. | Decisão tomada pelo Fernando, 09/11/2026. | Fernando, 2026-11-09 |