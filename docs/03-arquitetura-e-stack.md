# 03 · Arquitetura e stack

## 1. Princípios

1. **Somos uma camada adicional, não o caminho crítico.** Voz (Alexa/Smart Life), interruptores físicos e o app do fabricante continuam funcionando se **nossa** plataforma cair.
2. **Segredos só no servidor.** A Open API da Tuya exige assinar cada requisição com o *Access Secret* ([01](01-evidencias-e-pesquisa.md), T16): é impossível chamá-la direto do navegador sem expor a credencial.
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
| Custo recorrente por casa | n/a | Infra ≈ R$ 2–5 **+ Flagship US$ 25 mil/ano** ✅ (≈ R$ 11,5/casa/mês com 1.000 casas; ≈ R$ 115 com 100) | Infra + suporte; **sem taxa Tuya** nos dispositivos Zigbee; Wi-Fi/LAN ainda exige a `local_key`, que vem da conta de nuvem ✅ |
| Complexidade | Mínima | Média | Alta |
| Velocidade de desenvolvimento | Dias | **4–8 semanas até piloto** | 3–5 meses |
| Segurança | ⛔ Segredo exposto | Boa (segredos no servidor, RLS) | Boa; mais superfície (Edge Box, atualização remota) |
| Escalabilidade | Nenhuma | Limitada por **4 comandos/s por projeto** ✅ (seção 5) e pelo custo da Flagship | **A mais alta** |
| Dependência de terceiros | Total (Tuya + navegador) | **Alta: Tuya Cloud + internet** | Baixa (funciona na LAN sem internet) |
| Manutenção | n/a | Baixa | Média (drivers/firmware de dispositivos) |
| Margem | n/a | **Depende da taxa Tuya** | Melhor em escala |
| Experiência do cliente | Frágil | Boa; sem internet = sem painel | **Melhor**: rápida e resiliente |
| Expansão futura | Nenhuma | Boa, **se houver adapters desde o início** | Máxima |

### D · App próprio sobre o App SDK da Tuya (sem IoT Core)

Alternativa que as fontes oficiais revelaram: em vez de uma plataforma web falando com a Open API, **um app com a sua marca** feito com o *Smart Life App SDK* (*Self-Developed App*: **US$ 5 mil no 1º ano e US$ 2 mil depois, usuários ilimitados** ✅, [01](01-evidencias-e-pesquisa.md) T8). Pareamento (EZ/AP/QR/BLE), controle e contas ficam no SDK; o **painel 3D roda em WebView** dentro do app, com uma ponte para o SDK 🔬.

| Prós | Contras |
|---|---|
| Custo fixo baixo e **independente do número de casas** (a cota de 100 M é do SDK) | **Sem PWA/web**: exige app nativo/híbrido (iOS + Android), lojas e a ponte WebView↔SDK 🔬 |
| **Plug-and-play de verdade**: o pareamento nativo da Tuya dentro da sua marca (Nível 3 de [07](07-plug-and-play-e-instalacao.md)) | Sem IoT Core **não há API de nuvem no servidor**: cenas, automações e alertas dependem do app ou das cenas nativas da Tuya; sem motor próprio no servidor |
| Não passa pelo limite de 4 comandos/s do projeto de nuvem 🔬 | Dispositivos ficam na conta do **seu app**: a skill **Smart Life** da Alexa **não os enxerga**; a voz exige o serviço *Smart Voice* da Tuya (preço a pedir) ou skill própria |
| Dados e usuários na sua marca, com domínio próprio | Para ter também backend/Open API é preciso **somar o IoT Core (US$ 25 mil)** ✅ T9 |

A edição de **desenvolvimento** do App SDK é **gratuita** (≤ 100 usuários, 100 mil chamadas/mês) ✅ e permite prototipar o app sem pagar.

### Recomendação

**Arquitetura B no POC, desenhada com as costuras de C e D.** Backend próprio + Tuya Cloud como **primeiro** adaptador, com `ProviderAdapter` e modelo de dados independentes de fornecedor.

- **POC na sua casa com o Trial é exatamente o uso permitido** ("desenvolvedor individual / depuração"). **O Trial proíbe uso comercial** ✅ (T3): qualquer cliente, mesmo piloto pago, exige antes o **Portão 1**.
- É a única que entrega **POC em 3–5 semanas**; o piloto depende da resposta da Tuya.
- A Tuya é a maior incógnita **de preço e de contrato**: a interface de provedor é o **seguro** contra ela.
- O *Edge Box* e o app próprio só valem a pena **depois** do Portão 1.

**Regra de decisão no Portão 1** ([01](01-evidencias-e-pesquisa.md) §8): **B** (Flagship ou plano negociado) se custo e termos couberem; **D** se o produto puder ser centrado em app; **C** se a independência de nuvem for prioridade.

**Regra de migração B → C:** migrar quando (a) a Tuya não oferecer custo ≤ ~R$ 10/casa/mês **ou** o contrato não permitir uso em benefício de terceiros; (b) ≥ 10 casas ativas e > 1 incidente/mês por queda de nuvem; (c) fechaduras/segurança entrarem no escopo central; (d) o limite de 4 comandos/s virar gargalo.

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
- **Projeto Tuya do tipo *Smart Home*, no data center da conta** (Brasil: *Eastern America* para apps novos ✅; app Smart Life 🔬). A Tuya **proíbe chamadas vindas de outra região** (erro 2007 ✅): hospede o Core **nas Américas**.

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

Cálculos (cota oficial do Trial: 26 mil chamadas e 68 mil mensagens/mês ✅, T2; a Flagship tem 224 M e 568 M):

| Cenário | Consumo mensal | Contra a cota |
|---|---|---|
| Painel consultando 10 dispositivos a cada 10 s | **2.592.000** chamadas | **100×** a cota |
| Idem a cada 30 s | 864.000 | 33× |
| Uma tomada com medidor reportando a cada 10 s | **259.200 mensagens** | 3,8× a cota de mensagens |
| Uso real por comandos (≈ 40/dia numa casa) | 1.200 chamadas | 4,6 % |

Regras decorrentes: **estado vem de eventos**; consulta direta só *sob demanda* (ex.: botão "atualizar") e com limite; **medidores de energia** exigem atenção (frequência de relatório do firmware 🔬 — S3) e podem pesar nas **mensagens**.

### 5.1 O limite que decide a escala: 4 comandos por segundo **por projeto**

A tabela oficial de limites ✅ (T23) fixa, **por projeto de nuvem**: enviar propriedades **4/s**, enviar ações 4/s, ler propriedades 50/s, ler estado 5/s, **disparar cena 10/s**. Como todas as casas dividiriam o mesmo projeto, o limite é **global**.

| Cena de 8 ações disparada ao mesmo tempo em… | Tempo para drenar a fila a 4 comandos/s |
|---|---|
| 1 casa | 2 s |
| 10 casas | 20 s |
| 100 casas | 200 s (3 min 20 s) |
| 1.000 casas | 2.000 s (33 min) |

Mitigações (a validar no S1b; a tabela cobre as APIs v2.0, e a rota v1.0 de comandos não tem limite publicado):

1. **Fila com *token bucket* global** de 4/s por projeto, com prioridade: comando manual › cena › automação.
2. **Cenas nativas da Tuya** (disparo 10/s): **uma chamada executa N ações dentro da Tuya** 🔬.
3. **Escalonar automações** com *jitter* (ex.: "Boa noite" às 22:00 ± 5 min).
4. **Progresso visível** no 3D ("3 de 8") para que a espera não pareça falha.
5. **Edge local** para cenas (sem limite de nuvem) e **pedir limite maior** à Tuya (pergunta 4 do e-mail).

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
| **Banco / Auth / Realtime / Storage** | **Supabase** (Postgres) — **Pro a partir de US$ 25/mês** ✅ | RLS multi-tenant pronto, Auth, Realtime e Storage; schema portátil (Postgres puro). Alternativas: Neon/RDS + auth próprio; PocketBase só para POC |
| **Hospedagem** | Frontend: Cloudflare Pages · Core: Fly.io ou VPS **nas Américas** (US$ 5–15/mês) · Banco: Supabase **São Paulo (`sa-east-1`)** ✅ | Processo longo (Pulsar) não cabe em serverless; a Tuya veda chamadas de outra região (erro 2007); frontend estático é grátis |
| **APIs** | Tuya Open API + Message Service; (Fase 3) Alexa Smart Home *add-on* | Ver [04](04-integracao-tuya-e-alexa.md) |
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
| **Tuya suspende ou restringe o projeto** (o contrato, cl. 9, permite fazê-lo **sem aviso prévio** em vários casos ✅) | Painel e comandos param para **todas** as casas de uma vez | `ProviderAdapter`, plano B (D/C), ordem de serviço escrita, monitor de erros 28841xxx/1106 e comunicação ao cliente; Alexa/Smart Life continuam, pois dependem da conta, não do nosso projeto |
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
| 1–10 casas | Nenhum técnico; **contrato** (Trial proíbe uso comercial ✅) | Trial só na **sua** casa (depuração); Portão 1 antes de qualquer cliente |
| 100 casas | **Taxa fixa da Tuya** (≈ R$ 115/casa/mês no preço de tabela); **4 comandos/s**; suporte | Painel de saúde; fila com *token bucket*; infra ≈ R$ 5/casa/mês |
| 1.000 casas | Volume de eventos (≈ 15 M/mês); **Realtime: Pro = 500 conexões simultâneas e 500 msg/s** ✅ (10.000 e 2.500 sem *spend cap*); 4 comandos/s | Partições mensais + retenção; canal Realtime por casa; compute maior; cenas nativas/Edge |
| 10.000 casas | ≈ 150 M eventos/mês (~22 GB/mês); processo único de worker | Particionar workers por região/`org_id`; fila (NATS/Redis Streams); réplica de leitura; Edge Box para tirar carga da nuvem |

Cálculos de volume em [06](06-modelo-de-dados.md) §6 (premissa: 500 eventos/casa/dia).
