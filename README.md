# Escala — Coffee Shop Roster

SaaS de escalas de turnos para cafés independentes de Dublin. Gera a escala semanal respeitando as regras irlandesas de tempo de trabalho (descanso de 11h, pausas, keyholder no fecho) e exporta CSV/Excel/PDF.

- **App:** Python + Streamlit (`app.py`, `database.py`, `logic.py`, `billing_logic.py`); local em `http://localhost:8501`
- **Base de dados:** Supabase PostgreSQL, projeto `roster-cafe` (Frankfurt, Transaction pooler) em produção; SQLite `roster_cafe.db` em dev (não versionado)
- **Pagamentos:** Stripe (modo teste) + Edge Functions `create-checkout` e `stripe-webhook` em `supabase/functions`
- **Deploy do app:** Streamlit Cloud (repo `nandocaetano/roster-cafe`)
- **Landing:** `..\escala-landing` (Astro + Tailwind), Cloudflare Worker em `escala.madfrog.ie` (repo `nandocaetano/escala-landing`)
- **Marca:** escala ⬡ by Mad Frog Studios

Comece por `LEIA-ME.md`.

## Rodar localmente

```
pip install -r requirements.txt
streamlit run app.py   # porta 8501
```

Variáveis: ver `.env.example` e `cerebro/COFRE.md` (só nomes).