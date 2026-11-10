-- RLS Enable — 5 tables (applied 2026-11-09)
-- shifttemplates, weeklysetup, dateheadcountoverrides, pendingcredentials already have RLS on.
-- Service role bypasses RLS automatically — psycopg2 app unaffected.
-- Rollback: supabase/rls_rollback.sql

ALTER TABLE public.cafes          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.funcionarios   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rosters        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions  ENABLE ROW LEVEL SECURITY;
