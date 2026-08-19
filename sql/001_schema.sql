create table assets (
  id uuid primary key default gen_random_uuid(),
  ticker text unique not null,
  name text,
  asset_class text check (asset_class in ('equity','etf','crypto','fx')) default 'equity',
  sector text,
  is_active boolean default true
);

create table prices (
  asset_id uuid references assets(id),
  date date not null,
  open numeric, high numeric, low numeric,
  close numeric not null,
  adj_close numeric not null,
  volume bigint,
  source text,
  primary key (asset_id, date)
);
create index prices_date_brin on prices using brin (date);

create table models (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  algorithm text not null,
  hyperparameters jsonb,
  artifact_path text,
  trained_at timestamptz default now(),
  is_active boolean default false
);

create table eval_results (
  id bigint generated always as identity primary key,
  model_id uuid references models(id),
  metric jsonb,
  created_at timestamptz default now()
);

create table forecasts (
  id bigint generated always as identity primary key,
  model_id uuid references models(id),
  asset_id uuid references assets(id),
  forecast_date date not null,
  target_date date not null,
  horizon_days int not null,
  expected_return numeric,
  interval_low numeric,
  interval_high numeric,
  unique (model_id, asset_id, forecast_date, target_date)
);

create table rebalances (
  id bigint generated always as identity primary key,
  rebalance_date date not null,
  optimizer_config jsonb,
  rationale text
);

create table target_weights (
  rebalance_id bigint references rebalances(id),
  asset_id uuid references assets(id),
  weight numeric check (weight between 0 and 1),
  primary key (rebalance_id, asset_id)
);

create table portfolios (
  id uuid primary key default gen_random_uuid(),
  name text unique,
  created_at timestamptz default now()
);
insert into portfolios (name) values ('default');

create table portfolio_returns (
  portfolio_id uuid references portfolios(id),
  date date,
  net_return numeric,
  primary key (portfolio_id, date)
);

-- Later, add Supabase Auth users:
-- alter table rebalances add column owner uuid references auth.users(id);
-- enable row level security on rebalances;
-- create policy "own rows" on rebalances using (owner = auth.uid());