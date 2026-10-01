-- Testes de isolamento multi-tenant (RLS), permissões e comandos críticos.
-- Rodam como superusuário; cada consulta de teste assume um papel/usuário via t.q / t.dml.
\set ON_ERROR_STOP on

create schema t;
grant usage on schema t to public;

-- UUID determinístico a partir de um nome curto (também usável dentro do SQL de teste).
create function t.u(p_name text) returns uuid language sql immutable as $$ select md5(p_name)::uuid $$;

-- Executa uma consulta escalar como (papel, usuário). Devolve o texto do resultado ou 'err:<sqlstate>'.
create function t.q(p_user uuid, p_sql text, p_role text default 'authenticated') returns text
language plpgsql as $$
declare v text;
begin
  perform set_config('request.jwt.claim.sub', coalesce(p_user::text, ''), true);
  begin
    execute format('set local role %I', p_role);
    execute p_sql into v;
    reset role;
    return coalesce(v, '(null)');
  exception when others then
    reset role;
    return 'err:' || sqlstate;
  end;
end $$;

-- Executa DML com RETURNING e devolve quantas linhas foram afetadas (ou 'err:<sqlstate>').
create function t.dml(p_user uuid, p_sql text, p_role text default 'authenticated') returns text
language sql as $$
  select t.q(p_user, 'with x as (' || p_sql || ') select count(*)::text from x', p_role)
$$;

create function t.eq(p_name text, p_got text, p_want text) returns void language plpgsql as $$
begin
  if p_got is distinct from p_want then
    raise exception 'FALHOU: % — obtido [%], esperado [%]', p_name, p_got, p_want;
  end if;
  raise notice 'ok  - %', p_name;
end $$;

-- ------------------------------------------------------------------ fixtures
insert into auth.users (id, email)
select t.u(n), n || '@teste' from unnest(array[
  'inst1', 'inst2', 'support1', 'ownerA', 'memberA', 'editorA', 'unlockA', 'guestA', 'ownerB', 'ownerC']) as n;

insert into organizations (id, name, slug) values
  (t.u('O1'), 'Instalador Um', 'org-um'),
  (t.u('O2'), 'Instalador Dois', 'org-dois');

insert into org_members (org_id, user_id, role) values
  (t.u('O1'), t.u('inst1'), 'installer'),
  (t.u('O1'), t.u('support1'), 'support'),
  (t.u('O2'), t.u('inst2'), 'installer');

insert into homes (id, org_id, name) values
  (t.u('H1'), t.u('O1'), 'Apto 101'),
  (t.u('H2'), t.u('O1'), 'Apto 302'),
  (t.u('H3'), t.u('O2'), 'Casa');

insert into home_members (home_id, user_id, role, can_unlock, can_edit) values
  (t.u('H1'), t.u('ownerA'),  'owner',  false, false),
  (t.u('H1'), t.u('memberA'), 'member', false, false),
  (t.u('H1'), t.u('editorA'), 'member', false, true),
  (t.u('H1'), t.u('unlockA'), 'member', true,  false),
  (t.u('H1'), t.u('guestA'),  'guest',  false, false),
  (t.u('H2'), t.u('ownerB'),  'owner',  false, false),
  (t.u('H3'), t.u('ownerC'),  'owner',  false, false);

insert into devices (id, home_id, provider, external_id, name) values
  (t.u('D1'),  t.u('H1'), 'tuya', 'tuya_bulb_1', 'Lâmpada sala'),
  (t.u('D1L'), t.u('H1'), 'tuya', 'tuya_lock_1', 'Fechadura'),
  (t.u('D1T'), t.u('H1'), 'tuya', 'tuya_temp_1', 'Sensor T/H'),
  (t.u('D2'),  t.u('H2'), 'tuya', 'tuya_bulb_2', 'Lâmpada'),
  (t.u('D3'),  t.u('H3'), 'tuya', 'tuya_bulb_3', 'Lâmpada');

insert into capabilities (id, home_id, device_id, kind, provider_code, access, critical) values
  (t.u('C1'),  t.u('H1'), t.u('D1'),  'power',       'switch_led',       'rw', false),
  (t.u('CL'),  t.u('H1'), t.u('D1L'), 'lock',        'lock_motor_state', 'rw', true),
  (t.u('CT'),  t.u('H1'), t.u('D1T'), 'temperature', 'va_temperature',   'r',  false),
  (t.u('C2'),  t.u('H2'), t.u('D2'),  'power',       'switch_led',       'rw', false),
  (t.u('C3'),  t.u('H3'), t.u('D3'),  'power',       'switch_led',       'rw', false);

insert into capability_state (capability_id, home_id, value) values
  (t.u('C1'), t.u('H1'), 'true'), (t.u('CL'), t.u('H1'), '"locked"'), (t.u('CT'), t.u('H1'), '23.5'),
  (t.u('C2'), t.u('H2'), 'false'), (t.u('C3'), t.u('H3'), 'false');

insert into rooms (id, home_id, slug, name) values (t.u('R1'), t.u('H1'), 'sala', 'Sala');
insert into objects (id, home_id, room_id, slot_key, kind, label) values
  (t.u('OB1'), t.u('H1'), t.u('R1'), 'sala.luz_principal', 'light', 'Luz da sala'),
  (t.u('OBL'), t.u('H1'), t.u('R1'), 'entrada.porta',      'lock',  'Porta principal');
insert into object_bindings (home_id, object_id, capability_id, role) values
  (t.u('H1'), t.u('OB1'), t.u('C1'), 'primary'),
  (t.u('H1'), t.u('OBL'), t.u('CL'), 'primary');
insert into scenes (id, home_id, name) values (t.u('S1'), t.u('H1'), 'Boa noite');
insert into device_events (home_id, capability_id, value, occurred_at) values
  (t.u('H1'), t.u('C1'), 'true', now()), (t.u('H3'), t.u('C3'), 'true', now());

-- ------------------------------------------------------------------ isolamento de leitura
select t.eq('dono A vê só a própria casa', t.q(t.u('ownerA'), 'select count(*) from homes'), '1');
select t.eq('dono A não vê casa de outro cliente da mesma org', t.q(t.u('ownerA'), $q$select count(*) from homes where id = t.u('H2')$q$), '0');
select t.eq('dono B vê só a casa 2', t.q(t.u('ownerB'), 'select count(*) from homes'), '1');
select t.eq('instalador 1 vê as 2 casas da sua org', t.q(t.u('inst1'), 'select count(*) from homes'), '2');
select t.eq('instalador 1 não vê casa de outra org', t.q(t.u('inst1'), $q$select count(*) from homes where id = t.u('H3')$q$), '0');
select t.eq('instalador 2 vê só a casa 3', t.q(t.u('inst2'), 'select count(*) from homes'), '1');
select t.eq('suporte 1 vê as 2 casas da org', t.q(t.u('support1'), 'select count(*) from homes'), '2');
select t.eq('sem login não vê nada', t.q(null, 'select count(*) from homes'), '0');
select t.eq('dono A lê estados só da própria casa', t.q(t.u('ownerA'), 'select count(*) from capability_state'), '3');
select t.eq('dono C não lê estados da casa 1', t.q(t.u('ownerC'), $q$select count(*) from capability_state where home_id = t.u('H1')$q$), '0');
select t.eq('histórico: dono A vê só eventos da própria casa', t.q(t.u('ownerA'), 'select count(*) from device_events'), '1');
select t.eq('dono A vê o nome da org dona da casa (white-label)', t.q(t.u('ownerA'), 'select count(*) from organizations'), '1');

-- ------------------------------------------------------------------ escrita bloqueada / permitida
select t.eq('dono A não altera casa de outro cliente', t.dml(t.u('ownerA'), $q$update homes set name = 'x' where id = t.u('H2') returning 1$q$), '0');
select t.eq('cliente não escreve estado (sem GRANT)', t.dml(t.u('ownerA'), 'update capability_state set value = ''false'' returning 1'), 'err:42501');
select t.eq('instalador também não escreve estado', t.dml(t.u('inst1'), 'update capability_state set value = ''false'' returning 1'), 'err:42501');
select t.eq('cliente não lê credenciais de integração', t.q(t.u('ownerA'), 'select count(*) from integration_accounts'), 'err:42501');
select t.eq('service_role escreve estado', t.dml(null, $q$update capability_state set value = 'false' where capability_id = t.u('C1') returning 1$q$, 'service_role'), '1');

select t.eq('convidado lê cenas', t.q(t.u('guestA'), 'select count(*) from scenes'), '1');
select t.eq('convidado não cria cena', t.dml(t.u('guestA'), $q$insert into scenes (home_id, name) values (t.u('H1'), 'x') returning 1$q$), 'err:42501');
select t.eq('membro sem can_edit não cria cena', t.dml(t.u('memberA'), $q$insert into scenes (home_id, name) values (t.u('H1'), 'x') returning 1$q$), 'err:42501');
select t.eq('membro com can_edit cria cena', t.dml(t.u('editorA'), $q$insert into scenes (home_id, name) values (t.u('H1'), 'Cinema') returning 1$q$), '1');

select t.eq('instalador cadastra dispositivo na casa da própria org', t.dml(t.u('inst1'), $q$insert into devices (home_id, provider, external_id, name) values (t.u('H1'), 'tuya', 'novo1', 'Novo') returning 1$q$), '1');
select t.eq('instalador não cadastra em casa de outra org', t.dml(t.u('inst1'), $q$insert into devices (home_id, provider, external_id, name) values (t.u('H3'), 'tuya', 'novo2', 'Novo') returning 1$q$), 'err:42501');
select t.eq('suporte lê mas não escreve', t.dml(t.u('support1'), $q$insert into devices (home_id, provider, external_id, name) values (t.u('H1'), 'tuya', 'novo3', 'Novo') returning 1$q$), 'err:42501');
select t.eq('dono (cliente) não altera a estrutura de dispositivos', t.dml(t.u('ownerA'), $q$insert into devices (home_id, provider, external_id, name) values (t.u('H1'), 'tuya', 'novo4', 'Novo') returning 1$q$), 'err:42501');
select t.eq('dono (cliente) não muda o status da própria casa', t.dml(t.u('ownerA'), $q$update homes set status = 'suspended' where id = t.u('H1') returning 1$q$), 'err:42501');
select t.eq('dono (cliente) renomeia a própria casa', t.dml(t.u('ownerA'), $q$update homes set name = 'Meu apê' where id = t.u('H1') returning 1$q$), '1');

-- ------------------------------------------------------------------ integridade entre tenants (FK composta)
select t.eq('FK composta impede ligar objeto de uma casa a capacidade de outra',
  t.q(null, $q$insert into object_bindings (home_id, object_id, capability_id, role) values (t.u('H2'), t.u('OB1'), t.u('C1'), 'aux') returning 1$q$, 'postgres'),
  'err:23503');
select t.eq('FK composta impede capacidade apontando dispositivo de outra casa',
  t.q(null, $q$insert into capabilities (home_id, device_id, kind, provider_code) values (t.u('H2'), t.u('D1'), 'power', 'x') returning 1$q$, 'postgres'),
  'err:23503');

-- ------------------------------------------------------------------ comandos
select t.eq('membro comanda lâmpada',
  t.q(t.u('memberA'), $q$select (issue_command(t.u('C1'), '{"value":false}', t.u('REQ1')) is not null)::text$q$), 'true');
select t.eq('idempotência: mesmo request_id devolve o mesmo comando',
  t.q(t.u('memberA'), $q$select (issue_command(t.u('C1'), '{"value":true}', t.u('REQ2')) = issue_command(t.u('C1'), '{"value":true}', t.u('REQ2')))::text$q$), 'true');
select t.eq('idempotência: apenas 1 linha gravada', (select count(*)::text from commands where request_id = t.u('REQ2')), '1');
select t.eq('convidado comanda lâmpada',
  t.q(t.u('guestA'), $q$select (issue_command(t.u('C1'), '{"value":true}') is not null)::text$q$), 'true');
select t.eq('membro sem can_unlock NÃO comanda fechadura',
  t.q(t.u('memberA'), $q$select issue_command(t.u('CL'), '{"value":"unlock"}')::text$q$), 'err:42501');
select t.eq('convidado NÃO comanda fechadura',
  t.q(t.u('guestA'), $q$select issue_command(t.u('CL'), '{"value":"unlock"}')::text$q$), 'err:42501');
select t.eq('membro com can_unlock comanda fechadura',
  t.q(t.u('unlockA'), $q$select (issue_command(t.u('CL'), '{"value":"unlock"}') is not null)::text$q$), 'true');
select t.eq('dono comanda fechadura',
  t.q(t.u('ownerA'), $q$select (issue_command(t.u('CL'), '{"value":"lock"}') is not null)::text$q$), 'true');
select t.eq('comando crítico fica marcado na auditoria',
  (select bool_and(critical)::text from commands where capability_id = t.u('CL')), 'true');
select t.eq('capacidade somente leitura recusa comando',
  t.q(t.u('ownerA'), $q$select issue_command(t.u('CT'), '{"value":1}')::text$q$), 'err:42501');
select t.eq('outro tenant recebe a mesma resposta de "não existe"',
  t.q(t.u('ownerC'), $q$select issue_command(t.u('C1'), '{"value":true}')::text$q$), 'err:P0002');
select t.eq('anônimo não comanda',
  t.q(null, $q$select issue_command(t.u('C1'), '{"value":true}')::text$q$), 'err:28000');
select t.eq('cliente não insere comando direto na tabela',
  t.dml(t.u('ownerA'), $q$insert into commands (home_id, capability_id, payload, request_id) values (t.u('H1'), t.u('C1'), '{}', gen_random_uuid()) returning 1$q$), 'err:42501');
select t.eq('dono C não vê comandos da casa 1', t.q(t.u('ownerC'), 'select count(*) from commands'), '0');
select t.eq('dono A vê comandos da própria casa', t.q(t.u('ownerA'), 'select (count(*) > 0)::text from commands'), 'true');

-- ------------------------------------------------------------------ snapshot do painel
select t.eq('snapshot: 2 objetos', t.q(t.u('ownerA'), $q$select jsonb_array_length(home_snapshot(t.u('H1'))->'objects')::text$q$), '2');
select t.eq('snapshot: 3 estados', t.q(t.u('ownerA'), $q$select count(*)::text from jsonb_object_keys(home_snapshot(t.u('H1'))->'states')$q$), '3');
select t.eq('snapshot: objetos ordenados por slot; bindings trazem o tipo da capacidade',
  t.q(t.u('ownerA'), $q$select (home_snapshot(t.u('H1'))->'objects'->0->>'slot_key') || ':' || (home_snapshot(t.u('H1'))->'objects'->0->'bindings'->0->>'kind')$q$), 'entrada.porta:lock');
select t.eq('snapshot de outro tenant vem vazio (RLS)', t.q(t.u('ownerC'), $q$select jsonb_array_length(home_snapshot(t.u('H1'))->'objects')::text$q$), '0');

-- ------------------------------------------------------------------ partições de eventos
select t.eq('evento do mês atual não caiu na partição default', (select count(*)::text from only device_events_default), '0');
select ensure_event_partition(now()::date);   -- idempotente
select t.eq('partições mensais criadas (atual + 2)', (select count(*)::text from pg_inherits where inhparent = 'device_events'::regclass), '4');

do $$ begin raise notice 'TODOS OS TESTES PASSARAM'; end $$;
