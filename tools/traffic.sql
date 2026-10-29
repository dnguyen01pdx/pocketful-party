-- Page-view counter shared by medmapped.com (site = 'blog') and
-- atlas.medmapped.com (site = 'atlas'). Paste into the Supabase SQL editor;
-- safe to run again.
--
-- What a row holds: which site, the page path, the referring site's domain
-- (not the full URL), any utm_* tags on the link, a rough device size and the
-- time. No cookies, no IP address, no user agent, nothing that identifies a
-- person. Browsers may only INSERT; nobody can read rows through the public
-- key. Dylan reads the numbers in the Supabase dashboard (views below) or
-- through traffic_summary(), which returns totals only.

create table if not exists public.page_views (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  site text not null check (site in ('blog', 'atlas')),
  path text not null check (length(path) between 1 and 300),
  referrer text check (length(referrer) <= 200),
  utm_source text check (length(utm_source) <= 100),
  utm_medium text check (length(utm_medium) <= 100),
  utm_campaign text check (length(utm_campaign) <= 100),
  utm_content text check (length(utm_content) <= 100),
  device text check (device in ('mobile', 'tablet', 'desktop'))
);
create index if not exists page_views_site_time on public.page_views (site, created_at desc);

alter table public.page_views enable row level security;
revoke all on public.page_views from anon, authenticated;
grant insert (site, path, referrer, utm_source, utm_medium, utm_campaign, utm_content, device)
  on public.page_views to anon, authenticated;
drop policy if exists "anyone can record a view" on public.page_views;
create policy "anyone can record a view" on public.page_views
  for insert to anon, authenticated with check (true);

-- Dashboard views (Table Editor > Views). Not readable with the public key.
create or replace view public.traffic_daily with (security_invoker = on) as
  select (created_at at time zone 'America/New_York')::date as day, site, count(*) as views
  from public.page_views group by 1, 2 order by 1 desc, 2;

create or replace view public.traffic_top_pages_30d with (security_invoker = on) as
  select site, path, count(*) as views
  from public.page_views where created_at > now() - interval '30 days'
  group by 1, 2 order by 3 desc;

create or replace view public.traffic_sources_30d with (security_invoker = on) as
  select site, coalesce(utm_source, referrer, '(direct)') as source, count(*) as views
  from public.page_views where created_at > now() - interval '30 days'
  group by 1, 2 order by 3 desc;

revoke all on public.traffic_daily, public.traffic_top_pages_30d, public.traffic_sources_30d
  from anon, authenticated;

-- Totals for the med school hub's Business tab. Aggregates only.
create or replace function public.traffic_summary(days int default 30)
returns json language sql stable security definer set search_path = public as $$
  with v as (
    select * from page_views
    where created_at > now() - make_interval(days => least(greatest(days, 1), 365))
  )
  select json_build_object(
    'days', least(greatest(days, 1), 365),
    'totals', (select coalesce(json_object_agg(site, n), '{}') from
                (select site, count(*) n from v group by site) t),
    'today', (select coalesce(json_object_agg(site, n), '{}') from
                (select site, count(*) n from v
                 where (created_at at time zone 'America/New_York')::date
                     = (now() at time zone 'America/New_York')::date group by site) t),
    'daily', (select coalesce(json_agg(t order by t.day), '[]') from
                (select (created_at at time zone 'America/New_York')::date as day, site, count(*) as views
                 from v group by 1, 2) t),
    'top_pages', (select coalesce(json_agg(t), '[]') from
                (select site, path, count(*) as views from v group by 1, 2 order by 3 desc limit 15) t),
    'top_sources', (select coalesce(json_agg(t), '[]') from
                (select site, coalesce(utm_source, referrer, '(direct)') as source, count(*) as views
                 from v group by 1, 2 order by 3 desc limit 15) t),
    'devices', (select coalesce(json_object_agg(device, n), '{}') from
                (select coalesce(device, 'unknown') device, count(*) n from v group by 1) t)
  );
$$;
revoke all on function public.traffic_summary(int) from public;
grant execute on function public.traffic_summary(int) to anon, authenticated;
