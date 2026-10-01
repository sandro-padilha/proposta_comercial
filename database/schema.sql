-- =====================================================================================
-- Casa 3D — modelo de dados multi-tenant
-- PostgreSQL 15+ (testado no 16) · compatível com Supabase (usa auth.users e auth.uid())
--
-- Princípios
--   1. Tenant = organização (instalador/parceiro). Cada casa pertence a UMA organização.
--   2. Isolamento por RLS + FKs compostas (id, home_id): é impossível ligar um objeto de
--      uma casa a um dispositivo de outra, nem por engano de aplicação.
--   3. O cliente (papel `authenticated`) NUNCA escreve estado, eventos nem credenciais:
--      só o `service_role` (worker). Comandos passam por issue_command() (autorização + auditoria).
--   4. Segredos de integração ficam em integration_accounts, sem nenhum GRANT ao cliente.
--
-- Como aplicar: SQL Editor do Supabase (ou migration). Testes: database/tests/run.sh
-- =====================================================================================

-- ------------------------------------------------------------------ organizações e pessoas

create table organizations (
  id         uuid primary key default gen_random_uuid(),
  name       text not null,
  slug       text not null unique check (slug ~ '^[a-z0-9-]{3,40}$'),
  kind       text not null default 'installer' check (kind in ('platform', 'installer', 'partner')),
  branding   jsonb not null default '{}'::jsonb,       -- logo, cores (white-label)
  created_at timestamptz not null default now()
);

create table profiles (
  id           uuid primary key references auth.users (id) on delete cascade,
  display_name text,
  phone        text,
  locale       text not null default 'pt-BR',
  created_at   timestamptz not null default now()
);

create table org_members (
  org_id  uuid not null references organizations (id) on delete cascade,
  user_id uuid not null references auth.users (id) on delete cascade,
  role    text not null check (role in ('owner', 'admin', 'installer', 'support')),
  primary key (org_id, user_id)
);
create index on org_members (user_id);

-- ------------------------------------------------------------------ casas

create table homes (
  id                  uuid primary key default gen_random_uuid(),
  org_id              uuid not null references organizations (id),
  name                text not null,
  timezone            text not null default 'America/Sao_Paulo',
  mode                text not null default 'home' check (mode in ('home', 'away', 'night', 'vacation')),
  status              text not null default 'draft' check (status in ('draft', 'installing', 'active', 'suspended')),
  template_version_id uuid,                              -- FK adicionada após template_versions
  settings            jsonb not null default '{}'::jsonb,
  created_at          timestamptz not null default now()
);
create index on homes (org_id);

create table home_members (
  home_id     uuid not null references homes (id) on delete cascade,
  user_id     uuid not null references auth.users (id) on delete cascade,
  role        text not null check (role in ('owner', 'member', 'guest')),
  can_unlock  boolean not null default false,            -- comandos críticos (fechadura)
  can_edit    boolean not null default false,            -- cenas e automações
  primary key (home_id, user_id)
);
create index on home_members (user_id);

create table home_invites (
  id          uuid primary key default gen_random_uuid(),
  home_id     uuid not null references homes (id) on delete cascade,
  role        text not null check (role in ('member', 'guest')),
  token_hash  text not null unique,                      -- guarda só o hash do token do QR/link
  expires_at  timestamptz not null,
  accepted_by uuid references auth.users (id),
  accepted_at timestamptz,
  created_by  uuid references auth.users (id),
  created_at  timestamptz not null default now()
);
create index on home_invites (home_id);

-- ------------------------------------------------------------------ templates de residência (modelos 3D)

create table templates (
  id         uuid primary key default gen_random_uuid(),
  org_id     uuid references organizations (id) on delete cascade,   -- NULL = catálogo da plataforma
  slug       text not null,
  name       text not null,
  area_m2    numeric(6, 1),
  bedrooms   smallint,
  unique nulls not distinct (org_id, slug)
);

create table template_versions (
  id          uuid primary key default gen_random_uuid(),
  template_id uuid not null references templates (id) on delete cascade,
  version     int  not null,
  glb_path    text not null,                             -- caminho no Storage
  glb_sha256  text not null,
  manifest    jsonb not null,                            -- salas e slots: contrato com os nós do GLB
  published   boolean not null default false,
  created_at  timestamptz not null default now(),
  unique (template_id, version)
);

alter table homes
  add constraint homes_template_version_fk foreign key (template_version_id) references template_versions (id);

-- ------------------------------------------------------------------ ambientes e objetos 3D

create table rooms (
  id      uuid primary key default gen_random_uuid(),
  home_id uuid not null references homes (id) on delete cascade,
  slug    text not null,
  name    text not null,
  floor   smallint not null default 0,
  sort    smallint not null default 0,
  unique (id, home_id),
  unique (home_id, slug)
);

create table objects (
  id       uuid primary key default gen_random_uuid(),
  home_id  uuid not null references homes (id) on delete cascade,
  room_id  uuid,
  slot_key text not null,                                -- ex.: 'sala.luz_principal' = extras.slot do nó no GLB
  kind     text not null check (kind in (
             'light', 'plug', 'ac', 'tv', 'door', 'lock', 'window', 'contact', 'motion', 'presence',
             'climate_sensor', 'energy', 'curtain', 'fan', 'scene_button', 'other')),
  label    text not null,
  behavior jsonb not null default '{}'::jsonb,           -- opções do comportamento visual
  enabled  boolean not null default true,
  unique (id, home_id),
  unique (home_id, slot_key),
  foreign key (room_id, home_id) references rooms (id, home_id) on delete set null (room_id)
);

-- ------------------------------------------------------------------ integrações, dispositivos, capacidades

create table integration_accounts (
  id            uuid primary key default gen_random_uuid(),
  home_id       uuid not null references homes (id) on delete cascade,
  provider      text not null check (provider in ('tuya', 'alexa', 'virtual')),
  status        text not null default 'pending' check (status in ('pending', 'linked', 'error', 'revoked')),
  external_ref  text,                                    -- ex.: uid do usuário Tuya
  region        text,                                    -- ex.: 'us', 'eu'
  credentials   jsonb,                                   -- cifrado pela aplicação (envelope). Sem GRANT ao cliente.
  last_sync_at  timestamptz,
  created_at    timestamptz not null default now(),
  unique (id, home_id)
);

create table devices (
  id                     uuid primary key default gen_random_uuid(),
  home_id                uuid not null references homes (id) on delete cascade,
  integration_account_id uuid references integration_accounts (id) on delete set null,
  provider               text not null check (provider in ('tuya', 'alexa', 'virtual')),
  external_id            text not null,                  -- ex.: device_id da Tuya
  parent_device_id       uuid,                           -- ex.: controle remoto IR sob o hub IR
  category               text,                           -- ex.: código de categoria Tuya ('dj', 'mcs', 'wnykq'...)
  product_id             text,
  name                   text not null,
  online                 boolean not null default false,
  last_seen_at           timestamptz,
  meta                   jsonb not null default '{}'::jsonb,
  unique (id, home_id),
  unique (home_id, provider, external_id),
  foreign key (parent_device_id, home_id) references devices (id, home_id) on delete set null (parent_device_id)
);
create index on devices (home_id);

create table capabilities (
  id            uuid primary key default gen_random_uuid(),
  home_id       uuid not null,
  device_id     uuid not null,
  kind          text not null check (kind in (
                  'power', 'brightness', 'color_temp', 'color_rgb', 'hvac', 'lock', 'contact', 'motion',
                  'presence', 'temperature', 'humidity', 'battery', 'power_w', 'energy_kwh', 'button',
                  'ir_key', 'scene')),
  provider_code text not null,                           -- ex.: 'switch_led' (código DP da Tuya)
  access        text not null default 'rw' check (access in ('r', 'w', 'rw')),
  critical      boolean not null default false,          -- exige permissão extra (fechadura, portão)
  schema        jsonb not null default '{}'::jsonb,      -- min/max/step/scale/unit/enum da especificação
  unique (id, home_id),
  unique (device_id, provider_code),
  foreign key (device_id, home_id) references devices (id, home_id) on delete cascade
);
create index on capabilities (home_id);

create table object_bindings (
  id            uuid primary key default gen_random_uuid(),
  home_id       uuid not null,
  object_id     uuid not null,
  capability_id uuid not null,
  role          text not null default 'primary' check (role in ('primary', 'state', 'battery', 'aux')),
  sort          smallint not null default 0,
  unique (object_id, capability_id, role),
  foreign key (object_id, home_id) references objects (id, home_id) on delete cascade,
  foreign key (capability_id, home_id) references capabilities (id, home_id) on delete cascade
);
create index on object_bindings (home_id);

-- ------------------------------------------------------------------ estado atual e histórico

create table capability_state (
  capability_id uuid primary key,
  home_id       uuid not null,
  value         jsonb not null,
  updated_at    timestamptz not null default now(),
  source        text not null default 'event' check (source in ('event', 'poll', 'command', 'import')),
  foreign key (capability_id, home_id) references capabilities (id, home_id) on delete cascade
);
create index on capability_state (home_id);

create sequence device_events_id_seq;

-- Histórico particionado por mês. Sem FKs de propósito (volume alto); o worker valida os ids.
create table device_events (
  id            bigint not null default nextval('device_events_id_seq'),
  home_id       uuid not null,
  capability_id uuid not null,
  value         jsonb not null,
  occurred_at   timestamptz not null,
  received_at   timestamptz not null default now(),
  primary key (id, occurred_at)
) partition by range (occurred_at);
create index on device_events (home_id, occurred_at desc);
create index on device_events (capability_id, occurred_at desc);

create table device_events_default partition of device_events default;

create function ensure_event_partition(p_month date) returns void
language plpgsql as $$
declare
  v_start date := date_trunc('month', p_month)::date;
  v_end   date := (date_trunc('month', p_month) + interval '1 month')::date;
begin
  execute format(
    'create table if not exists %I partition of device_events for values from (%L) to (%L)',
    'device_events_' || to_char(v_start, 'YYYY_MM'), v_start, v_end);
end $$;

-- Pré-cria o mês atual e os dois próximos (agende ensure_event_partition mensalmente: pg_cron ou o worker).
select ensure_event_partition((date_trunc('month', now()) + make_interval(months => i))::date)
from generate_series(0, 2) as i;

-- ------------------------------------------------------------------ comandos (auditoria + idempotência)

create table commands (
  id            uuid primary key default gen_random_uuid(),
  home_id       uuid not null references homes (id) on delete cascade,
  capability_id uuid not null,
  issued_by     uuid references auth.users (id) on delete set null,
  channel       text not null default 'panel' check (channel in ('panel', 'scene', 'automation', 'alexa', 'system')),
  payload       jsonb not null,                          -- ex.: {"value": true}
  critical      boolean not null default false,
  status        text not null default 'queued' check (status in ('queued', 'sent', 'acked', 'failed', 'timeout')),
  error         text,
  request_id    uuid not null,
  created_at    timestamptz not null default now(),
  completed_at  timestamptz,
  unique (home_id, request_id),
  foreign key (capability_id, home_id) references capabilities (id, home_id) on delete cascade
);
create index on commands (home_id, created_at desc);

-- ------------------------------------------------------------------ cenas e automações

create table scenes (
  id         uuid primary key default gen_random_uuid(),
  home_id    uuid not null references homes (id) on delete cascade,
  name       text not null,
  icon       text,
  sort       smallint not null default 0,
  enabled    boolean not null default true,
  created_at timestamptz not null default now(),
  unique (id, home_id)
);

create table scene_actions (
  id            uuid primary key default gen_random_uuid(),
  home_id       uuid not null,
  scene_id      uuid not null,
  step          smallint not null default 0,             -- ações do mesmo passo rodam em paralelo
  capability_id uuid not null,
  command       jsonb not null,                          -- ex.: {"value": false}
  delay_ms      int not null default 0 check (delay_ms between 0 and 600000),
  unique (scene_id, step, capability_id),
  foreign key (scene_id, home_id) references scenes (id, home_id) on delete cascade,
  foreign key (capability_id, home_id) references capabilities (id, home_id) on delete cascade
);

create table automations (
  id                uuid primary key default gen_random_uuid(),
  home_id           uuid not null references homes (id) on delete cascade,
  name              text not null,
  enabled           boolean not null default true,
  trigger           jsonb not null,                      -- {"type":"state","capability_id":"…","to":true} | {"type":"time",…}
  conditions        jsonb not null default '[]'::jsonb check (jsonb_typeof(conditions) = 'array'),
  actions           jsonb not null check (jsonb_typeof(actions) = 'array'),
  cooldown_s        int not null default 60 check (cooldown_s >= 0),
  last_triggered_at timestamptz,
  created_by        uuid references auth.users (id) on delete set null,
  created_at        timestamptz not null default now()
);
create index on automations (home_id) where enabled;

-- ------------------------------------------------------------------ alertas, push, auditoria

create table alerts (
  id        uuid primary key default gen_random_uuid(),
  home_id   uuid not null references homes (id) on delete cascade,
  kind      text not null,
  severity  text not null default 'info' check (severity in ('info', 'warning', 'critical')),
  title     text not null,
  body      text,
  data      jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  acked_at  timestamptz,
  acked_by  uuid references auth.users (id)
);
create index on alerts (home_id, created_at desc);

create table push_subscriptions (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references auth.users (id) on delete cascade,
  endpoint   text not null unique,
  p256dh     text not null,
  auth       text not null,
  created_at timestamptz not null default now()
);

create table audit_log (
  id        bigint generated always as identity primary key,
  org_id    uuid,
  home_id   uuid,
  actor     uuid,
  action    text not null,
  entity    text,
  entity_id text,
  data      jsonb not null default '{}'::jsonb,
  at        timestamptz not null default now()
);
create index on audit_log (home_id, at desc);

-- =====================================================================================
-- Funções de autorização (SECURITY DEFINER: leem as tabelas sem recursão de RLS)
-- =====================================================================================

create function is_org_member(p_org uuid, p_roles text[] default null) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from org_members m
    where m.org_id = p_org and m.user_id = auth.uid() and (p_roles is null or m.role = any (p_roles)));
$$;

create function home_org(p_home uuid) returns uuid
language sql stable security definer set search_path = public as $$
  select org_id from homes where id = p_home;
$$;

create function is_home_member(p_home uuid, p_roles text[] default null) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from home_members hm
    where hm.home_id = p_home and hm.user_id = auth.uid() and (p_roles is null or hm.role = any (p_roles)));
$$;

-- Vê a casa: membro da casa OU equipe da organização dona.
create function can_access_home(p_home uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select is_home_member(p_home) or is_org_member(home_org(p_home));
$$;

-- Administra a casa: dono da casa OU owner/admin/installer da organização (support só lê).
create function can_manage_home(p_home uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select is_home_member(p_home, array['owner']) or is_org_member(home_org(p_home), array['owner', 'admin', 'installer']);
$$;

-- Configura a estrutura (ambientes, objetos, dispositivos, vínculos): só a equipe da organização.
-- O cliente final não deve quebrar o que o instalador montou.
create function can_configure_home(p_home uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select is_org_member(home_org(p_home), array['owner', 'admin', 'installer']);
$$;

-- Edita cenas/automações: quem administra OU membro com can_edit.
create function can_edit_home(p_home uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select can_manage_home(p_home) or exists (
    select 1 from home_members hm where hm.home_id = p_home and hm.user_id = auth.uid() and hm.can_edit);
$$;

create function can_unlock_home(p_home uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select can_manage_home(p_home) or exists (
    select 1 from home_members hm where hm.home_id = p_home and hm.user_id = auth.uid() and hm.can_unlock);
$$;

create function my_org_ids() returns setof uuid
language sql stable security definer set search_path = public as $$
  select org_id from org_members where user_id = auth.uid()
  union
  select h.org_id from home_members hm join homes h on h.id = hm.home_id where hm.user_id = auth.uid();
$$;

-- =====================================================================================
-- RPCs usadas pelo painel / API
-- =====================================================================================

-- Único caminho de escrita de comandos pelo cliente. Autoriza, audita e é idempotente por (home, request_id).
-- O worker (service_role) lê comandos 'queued', chama a Tuya e atualiza o status.
create function issue_command(
  p_capability uuid,
  p_payload    jsonb,
  p_request_id uuid default gen_random_uuid(),
  p_channel    text default 'panel'
) returns uuid
language plpgsql security definer set search_path = public as $$
declare
  v_home uuid; v_access text; v_critical boolean; v_id uuid;
begin
  if auth.uid() is null then
    raise exception 'não autenticado' using errcode = '28000';
  end if;

  select c.home_id, c.access, c.critical into v_home, v_access, v_critical
  from capabilities c where c.id = p_capability;

  -- Mesma resposta para "não existe" e "é de outro tenant": não vaza a existência do id.
  if v_home is null or not can_access_home(v_home) then
    raise exception 'capacidade não encontrada' using errcode = 'P0002';
  end if;
  if v_access = 'r' then
    raise exception 'capacidade somente leitura' using errcode = '42501';
  end if;
  if v_critical and not can_unlock_home(v_home) then
    raise exception 'comando crítico não permitido' using errcode = '42501';
  end if;

  insert into commands (home_id, capability_id, issued_by, channel, payload, critical, request_id)
  values (v_home, p_capability, auth.uid(), p_channel, p_payload, v_critical, p_request_id)
  on conflict (home_id, request_id) do update set request_id = commands.request_id
  returning id into v_id;

  return v_id;
end $$;

-- Carga inicial do painel em UMA chamada (respeita RLS: SECURITY INVOKER).
create function home_snapshot(p_home uuid) returns jsonb
language sql stable security invoker set search_path = public as $$
  select jsonb_build_object(
    'home', (select jsonb_build_object('id', h.id, 'name', h.name, 'mode', h.mode, 'timezone', h.timezone,
                                       'template_version_id', h.template_version_id)
             from homes h where h.id = p_home),
    'rooms', coalesce((select jsonb_agg(jsonb_build_object('id', r.id, 'slug', r.slug, 'name', r.name, 'floor', r.floor)
                                        order by r.sort) from rooms r where r.home_id = p_home), '[]'::jsonb),
    'objects', coalesce((
      select jsonb_agg(jsonb_build_object(
        'id', o.id, 'slot_key', o.slot_key, 'kind', o.kind, 'label', o.label, 'room_id', o.room_id,
        'behavior', o.behavior,
        'bindings', (select coalesce(jsonb_agg(jsonb_build_object(
                       'capability_id', b.capability_id, 'role', b.role, 'kind', c.kind, 'access', c.access,
                       'critical', c.critical) order by b.sort), '[]'::jsonb)
                     from object_bindings b join capabilities c on c.id = b.capability_id
                     where b.object_id = o.id)) order by o.slot_key)
      from objects o where o.home_id = p_home and o.enabled), '[]'::jsonb),
    'states', coalesce((select jsonb_object_agg(s.capability_id, jsonb_build_object('v', s.value, 'at', s.updated_at))
                        from capability_state s where s.home_id = p_home), '{}'::jsonb),
    'scenes', coalesce((select jsonb_agg(jsonb_build_object('id', sc.id, 'name', sc.name, 'icon', sc.icon)
                                         order by sc.sort) from scenes sc where sc.home_id = p_home and sc.enabled), '[]'::jsonb)
  );
$$;

-- =====================================================================================
-- RLS
-- =====================================================================================

alter table organizations        enable row level security;
alter table profiles             enable row level security;
alter table org_members          enable row level security;
alter table homes                enable row level security;
alter table home_members         enable row level security;
alter table home_invites         enable row level security;
alter table templates            enable row level security;
alter table template_versions    enable row level security;
alter table rooms                enable row level security;
alter table objects              enable row level security;
alter table integration_accounts enable row level security;   -- sem policies: só service_role
alter table devices              enable row level security;
alter table capabilities         enable row level security;
alter table object_bindings      enable row level security;
alter table capability_state     enable row level security;
alter table device_events        enable row level security;
alter table commands             enable row level security;
alter table scenes               enable row level security;
alter table scene_actions        enable row level security;
alter table automations          enable row level security;
alter table alerts               enable row level security;
alter table push_subscriptions   enable row level security;
alter table audit_log            enable row level security;

-- organizações / pessoas
create policy org_select on organizations for select to authenticated using (id in (select my_org_ids()));
create policy org_update on organizations for update to authenticated
  using (is_org_member(id, array['owner', 'admin'])) with check (is_org_member(id, array['owner', 'admin']));

create policy profiles_select on profiles for select to authenticated using (
  id = auth.uid() or exists (
    select 1 from home_members a join home_members b on a.home_id = b.home_id
    where a.user_id = auth.uid() and b.user_id = profiles.id)
  or exists (
    select 1 from home_members hm join homes h on h.id = hm.home_id
    where hm.user_id = profiles.id and is_org_member(h.org_id)));
create policy profiles_insert on profiles for insert to authenticated with check (id = auth.uid());
create policy profiles_update on profiles for update to authenticated using (id = auth.uid()) with check (id = auth.uid());

create policy org_members_select on org_members for select to authenticated using (is_org_member(org_id));
create policy org_members_write on org_members for all to authenticated
  using (is_org_member(org_id, array['owner', 'admin'])) with check (is_org_member(org_id, array['owner', 'admin']));

-- casas e membros
create policy homes_select on homes for select to authenticated using (can_access_home(id));
create policy homes_insert on homes for insert to authenticated
  with check (is_org_member(org_id, array['owner', 'admin', 'installer']));
create policy homes_update on homes for update to authenticated
  using (can_manage_home(id)) with check (can_manage_home(id) and org_id = home_org(id));

create policy home_members_select on home_members for select to authenticated using (can_access_home(home_id));
create policy home_members_write on home_members for all to authenticated
  using (can_manage_home(home_id)) with check (can_manage_home(home_id));
create policy home_members_leave on home_members for delete to authenticated
  using (user_id = auth.uid() and role <> 'owner');

create policy home_invites_all on home_invites for all to authenticated
  using (can_manage_home(home_id)) with check (can_manage_home(home_id));

-- templates
create policy templates_select on templates for select to authenticated
  using (org_id is null or is_org_member(org_id));
create policy templates_write on templates for all to authenticated
  using (org_id is not null and is_org_member(org_id, array['owner', 'admin']))
  with check (org_id is not null and is_org_member(org_id, array['owner', 'admin']));
create policy template_versions_select on template_versions for select to authenticated using (
  exists (select 1 from templates t where t.id = template_id
          and ((t.org_id is null and published) or (t.org_id is not null and is_org_member(t.org_id)))));
create policy template_versions_write on template_versions for all to authenticated
  using (exists (select 1 from templates t where t.id = template_id and t.org_id is not null
                 and is_org_member(t.org_id, array['owner', 'admin'])))
  with check (exists (select 1 from templates t where t.id = template_id and t.org_id is not null
                      and is_org_member(t.org_id, array['owner', 'admin'])));

-- estrutura da casa: lê quem acessa; escreve só a equipe da organização (instalador/admin/owner)
create policy rooms_select on rooms for select to authenticated using (can_access_home(home_id));
create policy rooms_write on rooms for all to authenticated
  using (can_configure_home(home_id)) with check (can_configure_home(home_id));

create policy objects_select on objects for select to authenticated using (can_access_home(home_id));
create policy objects_write on objects for all to authenticated
  using (can_configure_home(home_id)) with check (can_configure_home(home_id));

create policy devices_select on devices for select to authenticated using (can_access_home(home_id));
create policy devices_write on devices for all to authenticated
  using (can_configure_home(home_id)) with check (can_configure_home(home_id));

create policy capabilities_select on capabilities for select to authenticated using (can_access_home(home_id));
create policy capabilities_write on capabilities for all to authenticated
  using (can_configure_home(home_id)) with check (can_configure_home(home_id));

create policy bindings_select on object_bindings for select to authenticated using (can_access_home(home_id));
create policy bindings_write on object_bindings for all to authenticated
  using (can_configure_home(home_id)) with check (can_configure_home(home_id));

-- estado, histórico e comandos: cliente só lê
create policy state_select on capability_state for select to authenticated using (can_access_home(home_id));
create policy events_select on device_events for select to authenticated using (can_access_home(home_id));
create policy commands_select on commands for select to authenticated using (can_access_home(home_id));

-- cenas e automações: quem edita
create policy scenes_select on scenes for select to authenticated using (can_access_home(home_id));
create policy scenes_write on scenes for all to authenticated
  using (can_edit_home(home_id)) with check (can_edit_home(home_id));
create policy scene_actions_select on scene_actions for select to authenticated using (can_access_home(home_id));
create policy scene_actions_write on scene_actions for all to authenticated
  using (can_edit_home(home_id)) with check (can_edit_home(home_id));
create policy automations_select on automations for select to authenticated using (can_access_home(home_id));
create policy automations_write on automations for all to authenticated
  using (can_edit_home(home_id)) with check (can_edit_home(home_id));

-- alertas, push, auditoria
create policy alerts_select on alerts for select to authenticated using (can_access_home(home_id));
create policy alerts_ack on alerts for update to authenticated
  using (can_access_home(home_id)) with check (can_access_home(home_id));
create policy push_own on push_subscriptions for all to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy audit_select on audit_log for select to authenticated using (home_id is not null and can_manage_home(home_id));

-- =====================================================================================
-- GRANTs (mínimo necessário — não dependa dos privilégios padrão do Supabase)
-- =====================================================================================

revoke all on all tables in schema public from anon, authenticated;
revoke all on all sequences in schema public from anon, authenticated;
revoke execute on all functions in schema public from public, anon;

grant usage on schema public to authenticated, service_role;
grant all on all tables in schema public to service_role;
grant all on all sequences in schema public to service_role;
grant execute on all functions in schema public to service_role;

-- leitura
grant select on organizations, org_members, homes, home_members, templates, template_versions, rooms, objects,
                devices, capabilities, object_bindings, capability_state, device_events, commands,
                scenes, scene_actions, automations, alerts, audit_log, profiles to authenticated;
-- escrita pelo cliente (sempre filtrada por RLS)
grant insert, update, delete on rooms, objects, devices, capabilities, object_bindings, scenes, scene_actions,
                                automations, home_members, home_invites to authenticated;
grant select on home_invites to authenticated;
grant insert on homes to authenticated;
grant update (name, mode, timezone) on homes to authenticated;   -- status/template/settings: só via API (service_role)
grant insert, update on profiles to authenticated;
grant update (name, branding) on organizations to authenticated;
grant insert, update, delete on org_members to authenticated;
grant insert, update, delete on templates, template_versions to authenticated;
grant update (acked_at, acked_by) on alerts to authenticated;
grant select, insert, update, delete on push_subscriptions to authenticated;
-- integration_accounts: nenhum GRANT ao cliente (somente service_role)

grant execute on function is_org_member(uuid, text[]), home_org(uuid), is_home_member(uuid, text[]),
                          can_access_home(uuid), can_manage_home(uuid), can_configure_home(uuid), can_edit_home(uuid), can_unlock_home(uuid),
                          my_org_ids(), issue_command(uuid, jsonb, uuid, text), home_snapshot(uuid) to authenticated;
