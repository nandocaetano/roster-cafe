-- RLS Rollback — reverter rls_enable.sql

ALTER TABLE public.cafes          DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.users          DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.funcionarios   DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.rosters        DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions  DISABLE ROW LEVEL SECURITY;
