# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

App: Python / Streamlit (hosted on Streamlit Community Cloud)
Landing page: static HTML/CSS (artifact-first; future deploy to madfrog.ie or subdomain)
Database: PostgreSQL via Supabase (psycopg2 dual-backend; SQLite for local dev)
Payments: Stripe (test mode, Checkout + Webhooks via Supabase Edge Functions)

## Users

**Primary:** Owners and floor managers of independent coffee shops in Dublin, Ireland.
Situation: Managing 5–20 staff across variable weekly schedules, often on a phone between shifts or on Sunday evening with a spreadsheet open.
Job: Build a weekly staff rota that is fair, feasible, and legally compliant with Irish working time law — without spending a Sunday night on it and without getting caught out by a WRC inspection.

**Secondary (future):** Group owners with 2–5 café locations who need a single compliance view across all sites.

## Product Purpose

Roster Café generates WTI-compliant weekly staff schedules for independent Dublin cafés automatically.
It enforces the three rules Irish café managers most commonly get wrong under the Organisation of Working Time Act 1997:
- **11-hour rest gap** between shifts (clopening block — hard rule, not a warning)
- **Mandatory breaks** scheduled at correct thresholds (15 min after 4.5h; 30 min after 6h)
- **Keyholder on every closing shift** (Manager / Assistant Manager / Head Barista)

Success = a manager enters their team once and gets a legal, fair weekly roster in minutes, not hours. The roster can be exported to CSV, Excel, or PDF and used as a compliance record if the WRC asks.

## Positioning

The only café rota tool that blocks illegal clopenings, schedules mandatory breaks, and enforces keyholder-on-close automatically — before the schedule prints. Excel draws the grid; Roster Café draws the grid **and** enforces Irish working time law.

WRC record-keeping failures carry fines up to ~€1,900. A single messy case can cost more than years of €19.90/month. The product's compliance automation is the core mechanism, not a feature.

## Operating Context

- Managers typically build rosters once a week (Thursday–Sunday), on desktop or phone.
- Staff availability, contract hours, and roles are set once and updated when something changes.
- The CP-SAT solver (OR-Tools) generates the roster; the manager reviews and approves.
- Export formats: CSV, Excel, PDF. Roster history stored per tenant.
- The app requires login; each café is a separate tenant (multi-tenant, isolated by tenant_id).
- Deployment: Streamlit Community Cloud (free tier). DB: Supabase PostgreSQL, Frankfurt.
- Pricing: €39.90 one-time setup + €19.90/month. 7-day free trial, no card required.
- One licence per café location. Max 10 staff on base plan.

## Capabilities and Constraints

**Confirmed capabilities:**
- CP-SAT auto-scheduler with WTI hard constraints (C1–C7)
- Add-ons A+B: Fairness Score (CP-SAT objective) + Shift Preference Weighting
- Weekly overrides: Folga / Férias / Treinamento
- Export: CSV, Excel, PDF
- Roster History (gated — Pro only)
- Analytics Tab (gated — Pro only)
- Stripe Checkout + subscription management (Phase 8, in progress)
- Multi-tenant: each café isolated; superadmin creates tenants
- Role-based access: superadmin / admin

**Confirmed constraints:**
- 10-staff cap on base plan (dynamic via billing_logic.py)
- No anonymous access; every session requires login
- All DB queries must include tenant_id (security invariant — never bypass)
- Passwords: SHA-256 + 16-byte salt only; never plaintext
- STRIPE_SECRET_KEY via env var only; never hardcoded
- Streamlit free tier limits: single thread, no background jobs, 1GB RAM

**Undecided / future:**
- License key activation flow (Phase 8 continuation)
- Multi-Café Admin Panel (Phase 9–10; Group Owner role)
- Trial timer automation (currently manual via admin)
- Progressively priced packages (10/15/20 employee tiers)

## Brand Commitments

- **Studio:** Mad Frog (Dublin, Ireland) — indie studio brand for SaaS + APKs
- **Product name:** Roster Café / Roster.café
- **Voice:** Direct, operational, local. No HR jargon. Speaks the language of the café floor: clopening, keyholder, 11h, WRC, the working time act.
- **Contact:** caetanolaska@gmail.com (temporary; madfrog.ie in progress)
- **Tone in copy:** Plain English first. Compliance framing second. No enterprise sales language.

## Evidence on Hand

- `docs/GTM_STRATEGY.md` — full go-to-market strategy, cold email scripts, pricing rationale, conversion funnel targets
- `docs/ARCHITECTURE.md` — module map, DB schemas, billing section, CP-SAT solver spec
- `docs/ROADMAP.md` — phases 1–8 (1–7 complete; Phase 8 Stripe billing in progress)
- `docs/RULES.md` — multi-tenancy security invariants, Streamlit state guidelines
- Working app live on Streamlit Community Cloud (Supabase DB, real tenants)
- GROK (CMO agent) feedback on landing page copy stored in Maestri note "GROK Landing Feedback"
- No customer testimonials yet (pre-launch). No press. No case studies.

## Product Principles

1. **Compliance is not optional.** WTI rules are hard constraints, never soft warnings. A roster that violates the law must not be possible to generate.
2. **Floor-simple.** If a café manager needs training to use the app, the app failed. Every UI decision should pass the "busy Thursday morning" test.
3. **One licence, one café.** Isolation is both a security invariant and a business model. Each tenant's data is never visible to another.
4. **Earn the monthly.** The setup fee covers onboarding; the monthly is renewed by value delivered — legal rosters, saved Sunday nights, peace of mind at a WRC knock. No dark patterns.
5. **Small and defensible.** Dublin independent cafés only, for now. Depth of compliance (WTI-specific) beats breadth of market.

## Accessibility & Inclusion

No formal accessibility standard confirmed yet. Priority: mobile-readable on small phone screens (managers checking rosters on shift). Minimum: readable contrast, no tiny touch targets, no font-size below 14px.
