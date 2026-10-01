# 03 · Arquitetura e stack

## 1. Princípios

1. **Somos uma camada adicional, não o caminho crítico.** Voz (Alexa/Smart Life), interruptores físicos e o app do fabricante continuam funcionando se **nossa** plataforma cair.
2. **Segredos só no servidor.** A Open API da Tuya exige assinar cada requisição com o *Access Secret* ([01](01-evidencias-e-pesquisa.md), T11): é impossível chamá-la direto do navegador sem expor a credencial.
3. **Eventos em vez de polling.** O orçamento de cota torna o polling inviável (seção 5).
4. **Provedor por trás de uma interface (adapter).** Tuya Cloud é o primeiro adaptador; o segundo (local/Zigbee) entra sem reescrever painel, banco nem regras.
5. **Cena é dado.** Template GLB + manifesto + vínculos; nenhum código novo por cliente ([05](05-painel-3d-e-valor-percebido.md)).
6. **Comando crítico é caso especial** (fechadura): permissão extra, reautenticação, auditoria, nunca disparado por automação por padrão.
7. **Simplicidade operacional**: poucos serviços, gerenciados quando possível.

## 2. Arquiteturas comparadas

### A · Frontend 3D + Tuya Cloud direto
O navegador chama a Open API da Tuya.
**Inviável como produto:** exige o *Access Secret* no cliente. Só funciona como protótipo descartável com um *proxy* serverless, o que **já é a Arquitetura B simplificada**. Útil para um *spike* de 1–2 dias (ver uma lâmpada reagindo ao 3D).

### B · Frontend 3D + backend próprio + Tuya Cloud
Painel (PWA) → API/worker próprios → Tuya Cloud. Banco multi-tenant, eventos por Pulsar, cenas e automações no servidor.

### C · Frontend 3D + backend próprio + múltiplas plataformas
Igual a B, com vários adaptadores (Tuya Cloud, **Edge Box local** com Zigbee/LAN, Shelly/Sonoff, Matter…). O backend é um orquestrador de provedores.

| Critério | A · Direto | B · Backend + Tuya | C · Backend + multi-plataforma |
|---|---|---|---|
| Custo inicial | ≈ 0 | Baixo (R$ 150–250/mês de infra) | Médio (Edge Box ≈ R$ 300–600 por casa + engenharia) |
| Custo recorrente por casa | n/a | Infra ≈ R$ 2–5 **+ taxa Tuya (a definir; ver Portão 1)** | Infra + suporte; **sem taxa Tuya** nos dispositivos locais |
| Complexidade | Mínima | Média | Alta |
| Velocidade de desenvolvimento | Dias | **4–8 semanas até piloto** | 3–5 meses |
| Segurança | ⛔ Segredo exposto | Boa (segredos no servidor, RLS) | Boa; mais superfície (Edge Box, atualização remota) |
| Escalabilidade | Nenhuma | Alta até cotas/custos da Tuya | **A mais alta** |
| Dependência de terceiros | Total (Tuya + navegador) | **Alta: Tuya Cloud + internet** | Baixa (funciona na LAN sem internet) |
| Manutenção | n/a | Baixa | Média (drivers/firmware de dispositivos) |
| Margem | n/a | **Depende da taxa Tuya** | Melhor em escala |
| Experiência do cliente | Frágil | Boa; sem internet = sem painel | **Melhor**: rápida e resiliente |
| Expansão futura | Nenhuma | Boa, **se houver adapters desde o início** | Máxima |

### Recomendação

**Arquitetura B, desenhada com as costuras da C.** Isto é: backend próprio + Tuya Cloud como **primeiro** adaptador, com a interface `ProviderAdapter` e o modelo de dados já independentes de fornecedor. Motivos:

- É a única que entrega **POC em 3–5 semanas** e **piloto em 8–12**, que é o que valida o mercado.
- A taxa comercial da Tuya é a maior incógnita; uma interface de provedor é o **seguro** contra ela.
- O *Edge Box* só vale a pena construir **depois** do Portão 1 (resposta da Tuya) ou se o piloto mostrar que a falta de internet incomoda.

**Regra de migração B → C:** migrar quando (a) a Tuya não oferecer custo ≤ ~R$ 10/casa/mês, **ou** (b) ≥ 10 casas ativas e > 1 incidente/mês por queda de nuvem, **ou** (c) fechaduras/segurança entrarem no escopo central.

## 3. Arquitetura recomendada

```text
                         CLIENTE / INSTALADOR
                               │
                ┌──────────────┴───────────────┐
                │  PAINEL 3D  (PWA, React+R3F) │   Cloudflare Pages
                │  modo lista (fallback)       │   cache offline do GLB
                └───────┬─────────────▲────────┘
          HTTPS (JWT)   │             │ WebSocket (Realtime) · estado/eventos
                        ▼             │
         ┌──────────────────────────────────────────────┐
         │  SUPABASE  (Postgres + Auth + Realtime +     │
         │  Storage[GLB])  — RLS multi-tenant            │
         └──────▲───────────────────────────▲───────────┘
                │ service_role              │ NOTIFY/Realtime
        ┌───────┴───────────────────────────┴──────────┐
        │  CORE (Node + Fastify, 1 processo)            │   Fly.io / VPS
        │  ├─ API de comandos (valida → issue_command)  │
        │  ├─ Command bus (fila, timeout, retry)        │
        │  ├─ Normalizador DP → capability              │
        │  ├─ Motor de cenas e automações               │
        │  ├─ Alertas / Web Push                        │
        │  └─ ProviderAdapter                            │
        │       ├─ TuyaCloudAdapter  (REST + Pulsar WS)  │  ← MVP
        │       ├─ EdgeAdapter       (Zigbee/LAN local)  │  ← Fase 3 (plano B)
        │       └─ VirtualAdapter    (demos e testes)    │
        └───────┬───────────────────────────────────────┘
                │ HTTPS assinado (HMAC) + WSS
                ▼
          TUYA CLOUD ◄──────────────► dispositivos (Wi-Fi/Zigbee/IR)
                ▲
                │  skill "Smart Life" (nuvem↔nuvem)   ← caminho PARALELO de voz
              ALEXA
```

Pontos de atenção:

- **Alexa não está no caminho de dados.** Ela fala com a Tuya diretamente (skill Smart Life). Isso é uma *feature de resiliência*: voz funciona mesmo com o nosso servidor fora ([04](04-integracao-tuya-e-alexa.md)).
- O painel lê **do nosso banco**, não da Tuya: nenhuma abertura de painel consome cota da Tuya.

## 4. Fluxos de dados

### 4.1 Comando (ex.: ligar a luz da sala)

```text
Usuário toca na luz 3D
  → Painel: atualização otimista (acende em 0 ms), request_id = UUID
  → POST /v1/commands {capability_id, value, request_id}   (JWT do usuário)
  → Core: chama RPC issue_command() COM o JWT do usuário
        (autoriza por RLS/papel, bloqueia crítico sem permissão, grava em `commands`, idempotente)
  → Core: ProviderAdapter.execute() → Tuya Open API (assinatura HMAC, token em cache)
  → Tuya → dispositivo
  → commands.status = 'sent'
  ... o dispositivo reporta ...
  → Tuya Message Service (Pulsar/WebSocket) → Core (decifra, normaliza DP → capability)
  → UPSERT capability_state + INSERT device_events
  → Realtime → Painel (confirma; se não vier em ~5 s, reverte o otimismo e mostra "sem resposta")
```

Latência esperada: toque→luz ≈ 0,3–1,5 s ponta a ponta 🔬 (medir no S1).

### 4.2 Evento do dispositivo (ex.: porta aberta)

```text
Sensor → Tuya Cloud → Pulsar WS → Core: normaliza e grava estado/evento
  → Motor de automações avalia gatilhos indexados por capability_id
  → ação (cena/comando) e/ou alerta (Web Push) · tudo auditado
  → Realtime → painéis abertos
```

### 4.3 Abertura do painel
`GET manifest` + **uma** RPC `home_snapshot()` (objetos, vínculos, estados, cenas) + assinatura do canal Realtime da casa. Sem tocar na Tuya.

## 5. Orçamento de cota: por que *polling é proibido*

Cálculos (premissa: trial de 26 mil chamadas e 68 mil mensagens/mês; ver T2, 🟡):

| Cenário | Consumo mensal | Contra a cota |
|---|---|---|
| Painel consultando 10 dispositivos a cada 10 s | **2.592.000** chamadas | **100×** a cota |
| Idem a cada 30 s | 864.000 | 33× |
| Uma tomada com medidor reportando a cada 10 s | **259.200 mensagens** | 3,8× a cota de mensagens |
| Uso real por comandos (≈ 40/dia numa casa) | 1.200 chamadas | 4,6 % |

Regras decorrentes: **estado vem de eventos**; consulta direta só *sob demanda* (ex.: botão "atualizar") e com limite; **medidores de energia** exigem atenção (frequência de relatório do firmware 🔬 — S3) e podem pesar nas **mensagens**.

## 6. Interface de provedor (contrato)

```ts
export interface ProviderAdapter {
  readonly provider: 'tuya' | 'edge' | 'virtual';
  /** Lista dispositivos e capacidades já normalizadas, para o instalador importar. */
  discover(account: IntegrationAccount): Promise<DiscoveredDevice[]>;
  /** Executa um comando normalizado; erros tipados: offline | timeout | rejected | forbidden. */
  execute(cap: CapabilityRef, cmd: NormalizedCommand): Promise<CommandResult>;
  /** Estado sob demanda (usar com parcimônia por causa da cota). */
  snapshot(caps: CapabilityRef[]): Promise<Record<string, NormalizedValue>>;
  /** Fluxo contínuo de eventos normalizados (Pulsar, LAN, Zigbee…). */
  events(account: IntegrationAccount): AsyncIterable<NormalizedEvent>;
}
```

Tudo acima do adaptador fala **capacidades** (`power`, `brightness`, `hvac`, `lock`, `contact`…), nunca códigos Tuya.

## 7. API (superfície mínima)

| Método | Rota | Função |
|---|---|---|
| GET | `/v1/homes/:id/manifest` | Template (URL assinada do GLB), salas, slots, tema |
| RPC | `home_snapshot(home)` | Estado inicial em uma chamada |
| POST | `/v1/commands` | Comando com `request_id` idempotente |
| POST | `/v1/scenes/:id/run` | Executa cena |
| GET | `/v1/homes/:id/activity` | Linha do tempo (eventos + comandos) |
| POST | `/v1/install/homes` · `/:id/import` · `/:id/bind` · `/:id/identify` · `/:id/publish` | Console do instalador ([07](07-plug-and-play-e-instalacao.md)) |
| POST | `/v1/alexa/*` | Somente na Fase 3 (skill própria) |

## 8. Stack

| Camada | Escolha | Por quê / alternativa |
|---|---|---|
| **3D** | `three` 0.186 + `@react-three/fiber` 9.8 + `@react-three/drei` 10.7 | Modelo declarativo estado → visual; `frameloop="demand"`; maior ecossistema. Alternativa: Babylon.js 9 (mais pesado, ferramentas melhores, integração React menos natural) |
| **Frontend** | React 19 + TypeScript + Vite 8, `zustand` (estado), PWA com Workbox 7 | Rápido de desenvolver; PWA cobre celular/tablet/desktop; Capacitor 8 empacota depois |
| **Backend** | Node 22 + Fastify 5 + TypeScript (1 serviço: API + worker Pulsar + motor de cenas) | Mesmo idioma do front; WebSocket do Pulsar sem cliente nativo (`ws`); código de integração já validado em `poc/tuya-core` |
| **Banco / Auth / Realtime / Storage** | **Supabase** (Postgres) | RLS multi-tenant pronto, Auth, Realtime e Storage; schema portátil (Postgres puro). Alternativas: Neon/RDS + auth próprio; PocketBase só para POC |
| **Hospedagem** | Frontend: Cloudflare Pages · Core: Fly.io ou VPS (US$ 5–15/mês) · Banco: Supabase em **região São Paulo** 🟡 (confirmar disponibilidade; LGPD/latência) | Processo longo (Pulsar) não cabe em serverless; frontend estático é grátis |
| **APIs** | Tuya Open API + Message Service; (Fase 3) Alexa Smart Home Skill | Ver [04](04-integracao-tuya-e-alexa.md) |
| **Autenticação** | Supabase Auth (e-mail/OTP no MVP, MFA para instalador, *passkeys* depois) | Sem senhas para o cliente final |
| **Push/alertas** | Web Push (VAPID) via PWA; e-mail como reserva; WhatsApp como serviço pago futuro | iOS exige PWA instalada 🟡 |
| **Observabilidade** | Sentry (erros), logs estruturados, página de status | Planos gratuitos bastam no MVP |
| **Testes** | `node:test` (já usado), `psql` com RLS (já usado), Playwright para o painel | Mesma abordagem da referência: testes sem GPU |

## 9. Estrutura do projeto (monorepo)

```text
/apps
  /panel            # PWA: React + R3F, modo 3D e modo lista
  /installer        # Console do instalador (wizard)  → pode começar dentro do /panel
  /core             # Fastify: API, command bus, worker Pulsar, cenas/automações, alertas
/packages
  /domain           # Tipos de capacidade, valores normalizados, JSON Schemas (manifest, cenas)
  /providers
    /tuya           # ← poc/tuya-core vira isto (sign, client, pulsar, mapeamento de DPs)
    /edge           # (Fase 3) Zigbee/LAN
    /virtual        # Simulador para demos e testes
  /scene-engine     # Interpretador de cenas e automações (puro, testável)
  /three-kit        # Componentes 3D: behaviors (Light, Ac, Door…), câmeras, qualidade
/database
  schema.sql        # (existe) + migrations
  tests/            # (existe) RLS e comandos
/templates          # GLB + manifest.json por modelo de apartamento (fonte Blender em /3d-src)
/devices            # Catálogo homologado: SKUs, DPs, escalas, notas de instalação
/docs               # (existe) estudo e decisões (ADR)
```

## 10. Confiabilidade: perguntas do briefing

| Falha | O que acontece | Mitigação |
|---|---|---|
| **Internet do cliente cai** | Wi-Fi/Tuya Cloud inacessíveis: painel e Alexa não comandam; **interruptores físicos continuam** (com lâmpada inteligente, o interruptor de parede deve ficar ligado, ou usar botão sem fio Zigbee); cenas locais do gateway: 🔬 | PWA abre do cache e mostra *"sem conexão — último estado às 21:42"* com controles desabilitados e o motivo; guia de instalação com botões físicos; **Edge Box** (Fase 3) para LAN |
| **API Tuya indisponível** | Idem, mas só do lado nuvem | *Circuit breaker*; painel só-leitura com último estado; backoff; alerta interno; **comandos críticos nunca entram em fila de reenvio** |
| **Nosso servidor cai** | Painel não atualiza; **Alexa/Smart Life/app Tuya seguem funcionando** (caminho paralelo) | Redeploy automático, health-check, status page; automações críticas de segurança ficam **no dispositivo**, não no nosso servidor |
| **Navegador/app fecha** | Nada se perde: estado e automações vivem no servidor | Ao reabrir: snapshot + deltas; detecção de dados velhos por `updated_at` |
| **Alexa indisponível** | Painel e app Tuya não são afetados | Alexa nunca é dependência de função |
| **Dispositivo offline** | Tuya informa `online=false` | Selo "offline" no 3D, comando falha rápido com mensagem; reconciliação no evento de volta; alerta se > 24 h |

## 11. Segurança

| Tema | Decisão |
|---|---|
| Segredos Tuya | Apenas no servidor (variáveis de ambiente/secret manager). **Nunca no frontend.** Credenciais por casa, se existirem, **cifradas pela aplicação** em `integration_accounts` e sem nenhum GRANT ao cliente |
| Autenticação | Supabase Auth; MFA obrigatório para instalador/admin |
| Autorização | **RLS** por casa/organização + papéis (`owner`, `member`, `guest`; `owner/admin/installer/support` na organização) — 50 asserções de teste ([06](06-modelo-de-dados.md)) |
| Isolamento entre clientes | RLS + **FKs compostas `(id, home_id)`**: impossível vincular objeto de uma casa a dispositivo de outra, nem por bug da aplicação |
| Transporte | HTTPS/WSS; HSTS; CSP; **verificação TLS ligada** no Pulsar (o SDK Python da Tuya a desliga — não copiar) |
| Comandos críticos | `capabilities.critical = true`; exigem `can_unlock`; reautenticação (PIN) no cliente; *rate limit*; notificação a todos os donos a cada abertura; **sem fila de reenvio**; automação **nunca** abre por padrão; falha segura (porta permanece trancada) |
| Auditoria | Tabela `commands` (quem, canal, quando, resultado) + `audit_log` |
| Privacidade (LGPD) | Presença e eventos de porta revelam hábitos: minimização, retenção de 90 dias para eventos brutos, consentimento, exportação/exclusão, DPA com o cliente; operadores: Supabase, Tuya (nuvem nos EUA — transferência internacional), Amazon. **Validar com advogado** |

## 12. Escalabilidade

| Escala | Gargalo provável | Ação |
|---|---|---|
| 1–10 casas | Nenhum; cota da Tuya | Trial só até ~1 casa; Portão 1 antes de piloto pago |
| 100 casas | Mensagens/chamadas Tuya; suporte | Painel de saúde dos dispositivos; custo de infra ≈ R$ 5/casa/mês |
| 1.000 casas | Volume de eventos (≈ 15 M/mês); fan-out Realtime | Partições mensais + retenção; canal Realtime por casa; compute maior |
| 10.000 casas | ≈ 150 M eventos/mês (~22 GB/mês); processo único de worker | Particionar workers por região/`org_id`; fila (NATS/Redis Streams); réplica de leitura; Edge Box para tirar carga da nuvem |

Cálculos de volume em [06](06-modelo-de-dados.md) §6 (premissa: 500 eventos/casa/dia).
