# 06 · Modelo de dados e multi-tenant

Arquivos: [`database/schema.sql`](../database/schema.sql) (631 linhas, 23 tabelas + partições) e [`database/tests/`](../database/tests/). **Verificado em PostgreSQL 16 real: 50 asserções passam** (`bash database/tests/run.sh`).

## 1. Qual banco?

| Opção | Pontos fortes | Pontos fracos | Veredito |
|---|---|---|---|
| **PostgreSQL (via Supabase)** | Relacional + `jsonb`; **RLS** nativo para multi-tenant; Auth, Realtime e Storage prontos; FKs compostas; partições; SQL portátil | Realtime e custo crescem com escala | ✅ **Recomendado** |
| JSON em arquivos | Zero infra | Sem consulta, concorrência nem isolamento | Só para *manifestos de template* (versionados no Storage) |
| SQLite | Simples, embutido | Multi-tenant e tempo real são manuais | **Edge Box** (Fase 3), não a plataforma |
| Firebase / Firestore | Tempo real fácil | Consulta relacional pobre, regras de segurança complexas, custo por leitura em tempo real, lock-in | Não |
| PocketBase | Um binário, ótimo para POC | Isolamento multi-tenant e escala limitados | Só POC descartável |

**Combinação:** Postgres como fonte de verdade; `jsonb` onde a forma varia (`behavior`, `trigger`, `actions`, `manifest`); arquivos GLB e manifestos no Storage.

## 2. Mapa das entidades

```text
organizations ──< org_members >── auth.users
     │
     ├──< templates ──< template_versions  ◄───────────────┐
     │                                                      │
     └──< homes ──< home_members >── auth.users             │ homes.template_version_id
            │
            ├──< rooms
            ├──< objects ──< object_bindings >── capabilities >── devices >── integration_accounts
            │                                         │                         (credenciais; só service_role)
            │                                         ├── capability_state   (1:1, estado atual)
            │                                         └──< device_events     (histórico, particionado por mês)
            ├──< scenes ──< scene_actions >── capabilities
            ├──< automations
            ├──< commands >── capabilities           (auditoria + idempotência)
            ├──< alerts
            └──< home_invites
```

Mapeamento dos nomes do briefing:

| Briefing | Tabela | Notas |
|---|---|---|
| `home` | `homes` | Pertence a **uma** organização; `mode` (`home/away/night/vacation`), `status` |
| `rooms` | `rooms` | `slug` estável (`sala`), `floor` |
| `objects` | `objects` | `slot_key` humano (`sala.luz_principal`) = `extras.casa3d.slot` no GLB; `kind`; `behavior` (jsonb) |
| `devices` | `devices` | `provider` + `external_id` (id Tuya), `parent_device_id` (controle IR sob o hub), `category`, `online` |
| `capabilities` | `capabilities` | Unidade de controle/leitura: `kind` (`power`, `brightness`, `hvac`, `lock`, `contact`…), `provider_code` (DP Tuya), `access` (`r/w/rw`), `critical`, `schema` (min/max/escala da spec) |
| (vínculo) | `object_bindings` | Objeto ↔ capacidade, com `role` (`primary/state/battery/aux`) |
| `states` | `capability_state` + `device_events` | **Atual** (1 linha por capacidade) e **histórico** (particionado) |
| `scenes` | `scenes` + `scene_actions` | Passos paralelos por `step`, `delay_ms`, FK para capacidade |
| `automations` | `automations` | `trigger`/`conditions`/`actions` em `jsonb`, `cooldown_s` |
| `users` | `auth.users` + `profiles` + `org_members` + `home_members` | Pessoa ≠ papel; papel por organização e por casa |
| (extra) | `commands` | Cada comando: quem, canal, payload, crítico, status, idempotência |
| (extra) | `integration_accounts` | Conta Tuya por casa; **credenciais sem GRANT ao cliente** |

## 3. O vínculo objeto ↔ dispositivo, em SQL

```sql
-- Instalador: "este objeto 3D controla esta capacidade"
insert into object_bindings (home_id, object_id, capability_id, role)
values (:home, :obj_luz_sala, :cap_switch_led, 'primary'),
       (:home, :obj_luz_sala, :cap_bright,     'aux');
```

O painel carrega tudo numa chamada: `select home_snapshot(:home)` → `{home, rooms, objects[ {slot_key, kind, bindings[ {capability_id, role, kind, access, critical} ]} ], states{capability_id: {v, at}}, scenes}`. Tocar num objeto = ler seus `bindings` e emitir `POST /v1/commands` na capacidade `primary`.

## 4. Multi-tenant: autenticação, isolamento, permissões

**Modelo:** plataforma → **organizações** (instaladores/parceiros; `kind='platform'` para você) → **casas** → membros. O cliente final nunca vê outra casa; o instalador vê **todas as casas da própria organização**.

| Papel | Ver | Comando comum | Comando crítico | Cenas/automações | Estrutura (objetos, dispositivos, vínculos) | Membros/convites | Credenciais |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Cliente `owner` | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| Cliente `member` | ✅ | ✅ | só com `can_unlock` | só com `can_edit` | ❌ | ❌ | ❌ |
| Cliente `guest` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Org `installer` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Org `admin`/`owner` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Org `support` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `service_role` (worker) | tudo | — | — | — | — | — | ✅ (único) |

Garantias **de banco** (não dependem do código da aplicação):

1. **RLS** em todas as tabelas, com funções `SECURITY DEFINER` (`can_access_home`, `can_manage_home`, `can_configure_home`, `can_edit_home`, `can_unlock_home`) sem recursão.
2. **FKs compostas `(id, home_id)`**: um `object_binding` da casa A **não consegue** apontar para capacidade da casa B, mesmo por bug ou SQL manual (testado: erro `23503`).
3. **GRANTs mínimos**: o cliente (`authenticated`) **não** escreve `capability_state`, `device_events` nem `commands`; **não** tem acesso algum a `integration_accounts`.
4. **`issue_command()`** é o **único** caminho de comando: autentica, resolve a capacidade, devolve **o mesmo erro** para "não existe" e "é de outro tenant" (não vaza ids), exige `can_unlock` quando `critical`, recusa capacidade só de leitura, grava a auditoria e é **idempotente** por `(home_id, request_id)`.
5. O cliente só altera de `homes` as colunas `name`, `mode` e `timezone`; `status`, `template_version_id` e `settings` passam pela API (service role).

**Identificadores:** `uuid` (v4) opacos para tudo; `slot_key` humano e estável para objetos 3D; `provider + external_id` para dispositivos (unicidade **por casa**, para um instalador não descobrir ids de outro tenant por erro de duplicidade); `request_id` do cliente para idempotência.

**Autenticação:** Supabase Auth. Cliente final por e-mail/OTP (sem senha); instalador/admin com MFA; convite por QR/link com token **guardado só como hash** (`home_invites.token_hash`).

## 5. O que os 50 testes provam

| Grupo | Exemplos de asserção |
|---|---|
| Isolamento de leitura | Dono A vê só a casa A; dono B só a B; instalador da org 1 vê as 2 casas dela e **nenhuma** da org 2; sem login não vê nada; eventos e estados só da própria casa |
| Escrita bloqueada/permitida | Cliente não escreve estado nem lê credenciais; `service_role` escreve estado; convidado/membro sem `can_edit` não cria cena; instalador cadastra dispositivo só na própria org; suporte lê mas não escreve; dono **não** altera estrutura nem `status`, mas renomeia a casa |
| Integridade entre tenants | FK composta barra vínculo e capacidade entre casas |
| Comandos | Idempotência; crítico exige `can_unlock`; dono comanda; somente-leitura recusa; outro tenant = "não existe"; anônimo bloqueado; sem `INSERT` direto em `commands` |
| Snapshot | Painel carrega objetos/estados/bindings; outro tenant recebe vazio |
| Partições | Evento do mês atual não cai na partição *default*; criação idempotente |

Rodar: `bash database/tests/run.sh` (sobe um PostgreSQL temporário, aplica um *stub* do Supabase e o schema, e executa os testes).

## 6. Estado, histórico e escala

- **`capability_state`**: 1 linha por capacidade → leitura O(1) no painel.
- **`device_events`**: append-only, **particionado por mês**, **sem FKs** de propósito (volume); índices por `(home_id, occurred_at)` e `(capability_id, occurred_at)`. Pré-cria 3 meses; agendar `ensure_event_partition()` mensal (pg_cron ou o worker) e **descartar partições > 90 dias**. Se a partição *default* tiver linhas, algo falhou no agendamento.
- Para consumo/energia use **agregados horários** (tabela futura `energy_hourly`) em vez de reter leituras brutas por anos.

Volume (premissa: 500 eventos/casa/dia, ~150 B/linha):

| Casas | Eventos/dia | Eventos/mês | Tamanho bruto/mês |
|---:|---:|---:|---:|
| 100 | 50 mil | 1,5 M | ~0,2 GB |
| 1.000 | 500 mil | 15 M | ~2,3 GB |
| 10.000 | 5 M | 150 M | ~22 GB |

Com retenção de 90 dias, mesmo 10 mil casas ficam em dezenas de GB — confortável em Postgres gerenciado, desde que o *fan-out* de Realtime seja por canal de casa.

## 7. Limitações conhecidas e próximos passos

| Item | Situação |
|---|---|
| Aceitar convite (`accept_invite(token)`) | Tabela pronta; RPC a implementar (comparar hash, criar `home_members`, marcar aceite) |
| Cifrar `integration_accounts.credentials` | Cifrar na aplicação (envelope) ou via Vault/pgsodium; **nunca** em texto puro |
| Autorização do Realtime por casa | Configurar regras de canal privado (RLS em `realtime.messages`) 🟡 — confirmar na doc do Supabase |
| Desempenho das *policies* | Funções por linha são suficientes para o MVP; quando crescer, usar o padrão `(select auth.uid())` e índices por `home_id` |
| Trilha de auditoria de mudanças estruturais | `audit_log` existe; falta *trigger*/escrita pela API |
| Migrations | Adotar ferramenta (Supabase CLI) e versionar o `schema.sql` como migração inicial |
| Dados de teste | Há fixtures nos testes; criar *seed* de demonstração com o template do apartamento |
