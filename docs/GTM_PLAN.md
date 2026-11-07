# GTM Plan — Escala by Mad Frog Studio
> Versão 1.0 — 2026-11-07

---

## 1. Produto & Posicionamento

**Produto:** Escala

**Tagline:** O único gerador de escalas para cafés irlandeses com as regras WTI embutidas.

**Descrição:** Escala é um web app (Streamlit) desenvolvido pela Mad Frog Studio em Dublin para donos de cafés com 5 a 20 funcionários. Automatiza a criação de rotas semanais com cumprimento total da Working Time Ireland (WTI): descanso mínimo de 11 horas entre turnos, bloqueio de clopening, e aplicação obrigatória de keyholder em cada turno.

**Proposta de valor única:**
O dono monta a rota em 10 minutos e cumpre a lei sem planilhas, sem consultoria e sem erro humano.

**Perfil do cliente ideal (ICP):**
- Dono ou gestor de café em Dublin (1-3 lojas)
- 5 a 20 funcionários em tempo parcial ou integral
- Já usa Excel ou rota manual — sente a dor do compliance WTI
- Não tem HR dedicado
- Paga por ferramentas que poupam tempo real

**Diferencial competitivo:**
Nenhuma solução genérica (Deputy, Rotamaster, When I Work) tem as regras irlandesas embutidas. Escala não exige configuração — funciona para Dublin out of the box.

**URL do produto:** escala.madfrog.ie
**Studio:** Mad Frog Studio — Dublin, Ireland — madfrog.ie

---

## 2. Pricing & Trial Model

### Filosofia
Sem free tier. O produto tem valor imediato e resolve um problema legal real. O trial com cartão filtra leads sérios e elimina utilizadores que nunca convertem.

### Planos

| Plano | Preço | Acesso | Notas |
|---|---|---|---|
| Trial | €0 por 15 dias | Completo | Cartão obrigatório no signup |
| Pro Mensal | €20/mês | Completo | Cancel anytime |
| Pro Anual | €200/ano | Completo | Equivalente a 2 meses grátis |

### Regras do Trial
- Duração: 15 dias completos a partir da data de signup
- Cartão de crédito/débito obrigatório no momento do início do trial
- Acesso completo a todas as funcionalidades durante o trial
- No dia 16, a conta é bloqueada automaticamente sem upgrade confirmado
- Sem taxa de setup
- Cancel anytime — sem penalidade de saída antecipada

### Cobrança Pós-Trial
- Se não cancelar antes do dia 16: cobra-se automaticamente €20/mês (Stripe `trial_period_days=15`)
- O utilizador recebe email de aviso no dia 14 (ver secção 4)
- O utilizador recebe confirmação de cobrança no dia 15

---

## 3. Pricing Cards — Copy para Landing Page

### Card 1 — Trial (destaque)

**Headline:** Try Escala free for 15 days

**Subline:** Full access. Card required. Cancel before day 16 and pay nothing.

**Features:**
- Full roster automation
- WTI compliance (11h rest)
- Clopening block
- Keyholder enforcement
- Up to 20 employees
- PDF export
- Analytics
- Roster history

**CTA button:** Start free trial

**Trust line:** No charge for 15 days. €20/month after. Cancel anytime.

---

### Card 2 — Pro

**Headline:** Pro — €20/month

**Subline:** Or €200/year — 2 months free

**Features:**
- Full roster automation
- WTI compliance (11h rest)
- Clopening block
- Keyholder enforcement
- Up to 20 employees
- PDF export
- Analytics
- Roster history

**CTA button:** Get Pro

---

## 4. Onboarding Trial — Sequência de 15 Dias

Sequência de email acionada automaticamente no momento do signup. Objetivo: ativar o utilizador rapidamente, demonstrar valor concreto, e converter antes do dia 16.

| Dia | Assunto | Objetivo |
|---|---|---|
| Dia 0 | Your first Dublin roster in under 10 minutes | Ativação imediata — guiar o utilizador a criar a primeira rota |
| Dia 1 | Did your rota pass the 11-hour rest check? | Educar sobre WTI — mostrar o diferencial da verificação automática |
| Dia 3 | Is every shift covered by a keyholder? | Demonstrar keyholder enforcement — reforçar valor de compliance |
| Dia 7 | Week one: what's missing for your café? | Recolher feedback + manter engagement na primeira semana |
| Dia 14 | Your trial ends tomorrow. Here's what Escala did for you | Urgência + retrospetiva de valor — preparar conversão |
| Dia 15 | You're on Pro: your receipt and how to cancel | Confirmação de cobrança + instruções de cancel (trust building) |

**Notas de implementação:**
- Dias 0, 1, 3, 7, 14: emails de ativação e educação
- Dia 15: email transacional de cobrança via Stripe webhook
- Ferramenta sugerida: Resend (integração simples com Supabase + Stripe webhooks)

---

## 5. Canais de Aquisição — Dublin Launch

### Canal 1 — Visitas Presenciais Dublin 1-8

**Formato:** Visita física a cafés nas zonas Dublin 1 a 8, horário 14h-16h (depois do rush de almoço, antes do jantar)

**Pitch:** Demo ao vivo de 5 minutos com a equipa do próprio dono no café. Mostrar: criar rota em tempo real com os funcionários deles, verificar compliance WTI, exportar PDF.

**Proposta direta:** "Vejo que tens X funcionários. Queres ver a rota desta semana pronta em 10 minutos?"

**Orçamento:** €100/mês (transporte + material)

**Meta:** 6 a 10 trials com cartão por mês

**Por que funciona:** Donos de café compram de pessoas que aparecem fisicamente. A demo ao vivo com os dados deles remove toda a fricção de imaginação — eles veem o valor no momento.

---

### Canal 2 — Parceiros Contadores e Consultores RH

**Formato:** Parceria com contadores e consultores de RH que trabalham com cafés em Dublin. Comissão por cliente pago ativado.

**Comissão:** €40 por cliente que converte para Pro (pagamento único, sem recorrência)

**Argumento para o parceiro:** "Recomenda o Escala aos teus clientes cafés. Eles ficam em compliance WTI automaticamente, tu recebes €40 por cada um que ativa."

**Meta:** 3 a 5 clientes novos/mês a partir do mês 2

**Perfil do parceiro ideal:** Contadores que fazem payroll para restauração, consultores de RH especializados em hospitality irlandesa

---

### Canal 3 — Google Ads Local

**Formato:** Campanhas de pesquisa local no Google, geo-targeting Dublin

**Keywords alvo:**
- "café rota software Dublin"
- "WTI rota Ireland"
- "employee scheduling Dublin café"
- "rota compliance Ireland"

**Orçamento:** €10/dia (€300/mês)

**Regra de pausa:** Pausar campanha se o custo por trial (CPT) ultrapassar €35

**Meta:** 10 a 15 trials com cartão por mês

**Notas:** Começar com exact match nas keywords WTI — menor volume, maior intenção. Escalar para phrase match após validar CPT.

---

### Resumo de Canais

| Canal | Custo/mês | Trials/mês estimados | CPT estimado |
|---|---|---|---|
| Visitas presenciais | €100 | 6-10 | €10-17 |
| Parceiros (comissão) | €40/cliente | 3-5 | €40 (pós-conversão) |
| Google Ads | €300 | 10-15 | €20-30 |

---

## 6. Unit Economics

| Métrica | Valor |
|---|---|
| Preço Pro Mensal | €20/mês |
| Preço Pro Anual | €200/ano |
| LTV estimado (18 meses) | €360 |
| Custo de infraestrutura estimado | €200/mês |
| Break-even (clientes pagos) | 10 clientes |
| MRR no break-even | €200/mês |

### ARR por número de clientes

| Clientes pagos | ARR |
|---|---|
| 20 | €4.800 |
| 50 | €12.000 |
| 100 | €24.000 |

### Custo de Aquisição

- Canal presencial: ~€10-17 por trial
- Google Ads: ~€20-30 por trial (meta)
- Parceiros: €40 por cliente pago convertido

Com conversão de 25-30% de trial → Pro, o CAC efetivo fica bem abaixo do LTV de €360.

---

## 7. KPIs — Meses 1 a 3

| Métrica | Mês 1 | Mês 2 | Mês 3 |
|---|---|---|---|
| Trials iniciados (com cartão) | 20 | 40 | 60 |
| Taxa de conversão Trial → Pro | 25% | 30% | 30% |
| Clientes pagos acumulados | 5 | 15 | 30 |
| MRR | €100 | €300 | €600 |
| Churn estimado | <10% | <10% | <10% |

**Break-even de infraestrutura:** 10 clientes pagos = €200/mês MRR

**Marcos:**
- Mês 1: Validar produto-mercado. 5 pagantes confirmam que a proposta funciona.
- Mês 2: Escalar canais. 15 pagantes = break-even de infra atingido.
- Mês 3: Referências e word-of-mouth começam. 30 pagantes = €600 MRR.

---

## 8. Stack Técnica & Infra

### Aplicação
- **Framework:** Streamlit (Python)
- **Base de dados:** Supabase (PostgreSQL) — hosted
- **Deploy do app:** Streamlit Cloud (share.streamlit.io)
- **URL do produto:** escala.madfrog.ie

### Landing Page
- **Framework:** Astro + Tailwind CSS + Motion One
- **Hosting:** Cloudflare Pages
- **Domínio:** madfrog.ie (registado via Register365)
- **DNS:** Cloudflare (propagação em andamento)

### Infraestrutura de Domínio
- **Registrar:** Register365
- **DNS:** Cloudflare
- **Email:** hello@madfrog.ie (Register365 webmail)

### Pagamentos
- **Provider:** Stripe
- **Configuração trial:** `trial_period_days=15` via Stripe Subscriptions
- **Webhooks:** Stripe → Supabase (bloqueio de conta no fim do trial sem upgrade)
- **Estado atual:** test mode → passar para live mode antes do launch oficial

### Resumo de URLs
| Serviço | URL |
|---|---|
| Studio | madfrog.ie |
| Produto | escala.madfrog.ie |
| Email | hello@madfrog.ie |

---

## 9. Próximos Passos

Os próximos passos estão ordenados por dependência técnica e de negócio:

1. **DNS propagar (1-2h)** → Aguardar propagação completa do DNS no Cloudflare para activar o subdomínio escala.madfrog.ie

2. **Construir landing page Astro** → Criar landing page em escala.madfrog.ie com os pricing cards (secção 3), copy de posicionamento e CTA para trial. Deploy via Cloudflare Pages.

3. **Implementar paywall no app** → Adicionar lógica de bloqueio no Streamlit: verificar estado da subscrição Stripe via Supabase; bloquear acesso no dia 16 sem subscrição activa.

4. **Configurar Stripe trial** → Configurar produto/preço no Stripe com `trial_period_days=15`. Implementar webhook `customer.subscription.trial_will_end` (aviso dia 14) e `invoice.payment_failed` (bloqueio dia 16).

5. **Switch Stripe para live mode** → Requer aprovação explícita do utilizador antes de executar. Esta é uma acção financeira com efeito real — só activar com confirmação directa.

6. **Launch canais Dublin** → Iniciar em paralelo: visitas presenciais (agendar primeira semana), activar Google Ads (campanha estruturada com as keywords definidas), contactar primeiros parceiros contadores.

---

*Documento produzido por Mad Frog Studio — Dublin, Ireland*
*Versão 1.0 — 2026-11-07*
