# COFRE — índice de segredos do Escala

> **Só nomes e onde vivem. NUNCA valores.** Valores ficam no Bitwarden e nos painéis de cada serviço.

## Cofre

- Bitwarden EU — `vault.bitwarden.eu` — login `caetanolaska@gmail.com` — pasta **Escala**
- Conta EU nova, criada em 09/11/2026 (a anterior foi excluída). A pasta **Escala** precisa ser recriada nela.
- A senha-mestra do Bitwarden é só do Fernando e nunca é escrita em lugar nenhum.
- Login superadmin (seed) do app: ainda não está no Bitwarden; o Cofre vai salvar e avisar.

## Streamlit Cloud → Settings → Secrets (app)

| Nome | Para quê | Estado |
|---|---|---|
| `DATABASE_URL` | Postgres do Supabase `roster-cafe` (Transaction pooler) | configurado |
| `STRIPE_SECRET_KEY` | Stripe (modo teste) | configurado |
| 6 price IDs (Starter/Standard/Plus × mensal/anual) | Checkout Stripe | configurados |
| `APP_URL` | URL pública do app | configurado |

## Supabase `roster-cafe` → Edge Function secrets

| Nome | Para quê | Estado |
|---|---|---|
| `STRIPE_SECRET_KEY` | `create-checkout` / `stripe-webhook` | configurado (teste) |
| `STRIPE_WEBHOOK_SECRET` | assinatura do webhook Stripe | configurado (corrigido 2026-11) |
| `RESEND_API_KEY` | e-mail de boas-vindas via Resend | configurado |

## Pendente

- Rotação antes do go-live: senha da base do Supabase e credenciais do admin (aprovação do Fernando)
- Troca das chaves Stripe de teste por live (aprovação do Fernando)
- Local: não há `.env`; ver `.env.example` (só nomes)