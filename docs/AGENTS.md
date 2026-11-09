# AGENTS — quem é quem no Escala

Canvas Maestri: "Coffe Shop Roster - MicroSas".

| Agente (nome no canvas) | Ferramenta | Papel |
|---|---|---|
| Claude - Maestro | Claude Code | Maestro / diretor técnico: lê o Cérebro, decide arquitetura e prioridade, escreve briefs, revisa, documenta (`/maestro-start`, `/maestro-save`) |
| Codex -Algorithm & Logic Specialist | Codex | Algoritmo e lógica: solver CP-SAT, regras WTI, código Python/Streamlit por brief |
| Grok - CMO & Growth Hacker | Grok | CMO / growth: copy da landing, preços (dentro do D-003), e-mails, GTM. Sempre em inglês para o mercado irlandês |

## Canal

- Delegar: `maestri ask "<nome exato do agente>" "<brief>"`
- Reportar de volta: `maestri ask "Claude - Maestro" "<resultado>"`
- Ver quem está ligado: `maestri list`
- Um agente por vez nos mesmos ficheiros. Quem revisa nunca é quem fez.

## Sempre com aprovação do Fernando

- Push para o GitHub e qualquer deploy (Streamlit Cloud, Cloudflare, Edge Functions)
- Pagamentos, Stripe em modo live, mudanças de billing que afetem clientes
- Qualquer contato com clientes (e-mails, mensagens)
- Gastos, compras, instalações de ferramentas ou pacotes novos
- Apagar qualquer coisa (o que é antigo vai para `C:\MadFrog\arquivo`)
- Rotação ou criação de credenciais

Antes de qualquer tarefa: seguir a ordem de leitura do `LEIA-ME.md`.