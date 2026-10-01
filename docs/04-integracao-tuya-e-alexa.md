# 04 · Integração Tuya e Alexa

Selos: ✅ confirmado · 🟡 provável · 🔬 necessita teste · ⛔ não recomendado ([01](01-evidencias-e-pesquisa.md)).

## 1. Cinco caminhos de acesso à Tuya

| Rota | O que é | Quando usar | Selo |
|---|---|---|---|
| **A. Projeto de nuvem (Open API + Message Service)** | Conta no console Tuya, projeto, assinatura *IoT Core* + *Message Service*, vínculo da conta Smart Life do cliente por QR | **POC e 1ª casa** (trial grátis). Escala comercial só após Portão 1 | Técnica ✅ · termos 🟡 |
| **B. App próprio (App SDK / "Self-Developed App")** | App com sua marca: contas, pareamento (EZ/AP/QR) e controle dentro do seu app; Open API para os usuários dele | **Melhor plug-and-play comercial**; custo reportado US$ 5 mil (1º ano) / US$ 2 mil (renovação) | 🟡 |
| **C. Device Sharing (QR + User Code do HA)** | Mecanismo do Home Assistant | — | ⛔ credenciais e rotas são do HA ([01](01-evidencias-e-pesquisa.md), T9) |
| **D. Controle local (LAN)** | `tinytuya`/`tuyapi` (MIT) com `local_key`; protocolos 3.1–3.5; 1 conexão TCP por dispositivo; **não** funciona com dispositivos a bateria | Núcleo do **Edge Box**; fallback sem internet | ✅ |
| **E. Zigbee aberto** | Dispositivos Zigbee (inclusive de marca Tuya) num coordenador seu, com `zigbee-herdsman` (MIT) | Elimina a taxa de nuvem; Edge Box | Licenças ✅ · compatibilidade por modelo 🔬 |

> **Decisão:** POC e piloto inicial na **Rota A**, desenhado para migrar para **B** (se a Tuya confirmar custo viável) ou **D+E** (Edge Box) se não. O código fica atrás do `ProviderAdapter` ([03](03-arquitetura-e-stack.md)).

## 2. Passo a passo da Rota A (POC)

1. **Console Tuya**: criar conta de desenvolvedor, criar **Cloud Project**, escolher o **data center** que casa com a região do app Smart Life. Para o Brasil o esperado é o das Américas (`https://openapi.tuyaus.com`) 🔬 — o erro mais comum é data center errado; a Tuya "proibirá chamadas entre regiões" ✅.
2. **Serviços**: assinar *IoT Core* (trial) e *Message Service*, e autorizar os grupos de API necessários (gestão/status/controle de dispositivos, infravermelho, etc.) 🔬 *(os nomes exatos estão no console; conferir no S1)*. Copiar **Access ID** e **Access Secret**.
3. **Dispositivos**: parear tudo no app **Smart Life** com nomes no padrão `Ambiente · Função` (ex.: `Sala · Luz principal`). Ver [07](07-plug-and-play-e-instalacao.md).
4. **Vínculo**: no projeto, *Devices → Link Tuya App Account → Add App Account* e escanear o QR com o app Smart Life. **É manual e feito no console, por conta** — é o principal gargalo de plug-and-play desta rota. Uma conta de app só pode estar em 2 projetos 🟡.
5. **Importação**: o backend lista os dispositivos (`GET /v1.0/iot-03/devices`) e, para cada um, lê `…/{id}/specification` (tipos, mín/máx/escala/enum) ✅.
6. **Eventos**: iniciar o `PulsarConsumer` no tópico `event` ✅.
7. **Comandos**: `POST /v1.0/iot-03/devices/{id}/commands` com `{"commands":[{"code","value"}]}` 🟡 (confirmar no S1), e as rotas de IR ✅.
8. **Validar**: spikes S1–S3 ([01](01-evidencias-e-pesquisa.md) §4).

### Código (já validado contra o SDK oficial)

`poc/tuya-core` — 22 testes; assinatura, token/refresh, comandos, IR e consumidor Pulsar:

```ts
import { TuyaClient, PulsarConsumer, TUYA_API_ENDPOINTS, TUYA_PULSAR_ENDPOINTS } from './src/index.ts';

const tuya = new TuyaClient({
  endpoint: TUYA_API_ENDPOINTS.us,           // data center do app (🔬 confirmar para BR)
  clientId: process.env.TUYA_CLIENT_ID!,
  secret: process.env.TUYA_SECRET!,           // nunca no frontend
});

await tuya.sendCommands(deviceId, [{ code: 'switch_led', value: true }]);          // luz
await tuya.acScene(irHubId, acRemoteId, { power: 1, mode: 1, temp: 24, wind: 1 });  // ar-condicionado por IR

new PulsarConsumer({
  accessId: process.env.TUYA_CLIENT_ID!,
  secret: process.env.TUYA_SECRET!,
  wsEndpoint: TUYA_PULSAR_ENDPOINTS.us,
  onEvent: (evt) => normalizeAndStore(evt),   // {devId, status:[{code,value,t}]}
  onError: (err) => log.error(err),
}).start();
```

Diferenças deliberadas em relação ao SDK Python: **verificação TLS ligada**, ACK sempre (sem laço de reentrega), reconexão com backoff, *single-flight* de token, corpo assinado = corpo enviado.

## 3. Normalização: código Tuya → capacidade

Os **códigos de DP** abaixo existem no código do HA (✅ nomes); a semântica e a **escala** devem sempre vir da `specification` do dispositivo — **nunca fixe escalas no código**.

| Capacidade (nossa) | Códigos Tuya típicos | Observações |
|---|---|---|
| `power` | `switch_led`, `switch_1`, `switch` | booleano |
| `brightness` | `bright_value_v2`, `bright_value` | converter para 0–100 % pelo mín/máx da spec |
| `color_temp` / `color_rgb` | `temp_value_v2`, `colour_data_v2`, `work_mode` | lâmpadas RGB têm modos branco/cor |
| `contact` | `doorcontact_state` | **polaridade** (true = aberto?) 🔬 S3 |
| `motion` / `presence` | `pir`, `presence_state` | radar mmWave costuma ter DPs extras 🔬 |
| `temperature` / `humidity` | `va_temperature`, `va_humidity`, `temp_current`, `humidity_value` | dividir pela escala da spec |
| `battery` | `battery_percentage` | alerta < 20 % |
| `power_w` / `energy_kwh` | `cur_power`, `cur_current`, `cur_voltage`, `add_ele` | frequência de relatório 🔬 (pesa em mensagens) |
| `hvac` (IR) | `/air-conditioners/…/scenes/command` → `power, mode, temp, wind` | **ver §4: estado é presumido** |
| `lock` | varia por modelo (`lock_motor_state`, `closed_opened`…) | 🔬 por modelo |

**Categorias de produto** (`category`): `dj` luz · `kg` interruptor · `cz` tomada · `mcs` sensor de porta/janela · `pir` movimento · `wsdcg` temperatura/umidade · `zndb` medidor · `kt` ar-condicionado · `wnykq` hub IR · `hps` presença · `ms`/`msp`/`jtmspro` fechaduras · `cl`/`clkg` cortinas · `wxkg`/`cjkg` botões/cenas · `sgbj` sirene · `ywbj` fumaça. Os códigos existem no HA ✅; as descrições são 🟡.

## 4. Infravermelho: o que ele **não** sabe

Rotas confirmadas ✅ (integração `tuya-smart-ir-ac`):

| Ação | Rota |
|---|---|
| Ar-condicionado — comando único | `POST /v2.0/infrareds/{ir}/air-conditioners/{ac}/command` `{code, value}` |
| Ar-condicionado — estado completo | `POST …/air-conditioners/{ac}/scenes/command` `{power, mode, temp, wind}` |
| Estado presumido | `GET /v2.0/infrareds/{ir}/remotes/{ac}/ac/status` · lote `GET /v1.0/cloud/rc/infrared/ac/status/batch?device_ids=…` |
| Controle genérico (TV etc.) | `GET …/remotes/{id}/keys` · `POST …/remotes/{id}/raw/command` `{category_id, key_id, key}` |

**IR é um canal de mão única.** O "estado" do ar ou da TV no 3D é **presumido** (o último comando enviado). Se alguém usar o controle físico, o 3D diverge. Decisões:

- Marcar visualmente como **"estado presumido"** (ícone sutil).
- **TV:** inferir pelo **consumo** com uma tomada com medidor (TV ligada ≈ dezenas de watts; em espera ≈ < 1 W) — solução barata e bem vista.
- **Ar:** sensor de temperatura no ambiente + consumo, quando houver.
- Instalar o hub IR com **linha de visada** e testar a marca do split (biblioteca de códigos da Tuya) antes de prometer.

## 5. Sensores, energia, cenas e automações

- **Sensores Wi-Fi a bateria** dormem e não mantêm conexão local ✅ (tinytuya): só chegam pela nuvem. **Sensores Zigbee** dependem do gateway; se ele os expõe localmente é 🔬. Preferir **Zigbee** (bateria e custo) com gateway.
- **Energia:** começar por **tomadas com medidor** (R$ 35–130, sem eletricista). Medidor de circuito (quadro) só no pacote Premium e **com eletricista** (NBR 5410).
- **Cenas no nosso motor**, não nas cenas nativas da Tuya: ações paralelas por passo, `delay_ms`, resultado por ação, falha parcial reportada. Cenas nativas da Tuya continuam existindo para a Alexa/Smart Life, mas **não** são nossa fonte de verdade (evita duplicidade).
- **Automações simples** no servidor: gatilho (estado/horário/pôr do sol) + condição (janela de horário, `home.mode`) + ação (cena/comando/alerta) + `cooldown`. Detalhes em [08](08-mvp-custos-negocio-riscos.md).
- **"Ninguém em casa"**: no MVP é um **modo da casa** (`home/away/night/vacation`) acionado por cenas (*Saí*, *Cheguei*, *Boa noite*), não por geofence (iOS em PWA não é confiável 🔬).

## 6. Fechadura (MVP 2, com teste prévio por modelo)

- Rota de abertura remota: `password-ticket` → `password-free/open-door` 🟡. Depende de **modelo de fechadura e gateway** compatíveis e talvez de **serviço adicional** 🔬. **Teste o modelo exato antes de comprar lote** (S4).
- Mercado BR: fechaduras com app Tuya/Smart Life de **R$ 318 a R$ 1.780** 🟡 (ex.: Aliança Titan Ultra com Wi-Fi).
- Salvaguardas (obrigatórias): `can_unlock`, PIN/biometria no cliente, *rate limit*, notificação a todos os donos, **sem reenvio automático**, **nenhuma automação abre por padrão**, falha segura, chave física sempre disponível, termo de responsabilidade e atenção a **imóvel alugado** (troca de cilindro exige anuência do proprietário).

## 7. Limites e custos Tuya (resumo)

| Item | Valor | Selo |
|---|---|---|
| Trial: dispositivos | 50 conectados / 10 controláveis | 🟡 |
| Trial: cotas | 26 mil chamadas e 68 mil mensagens/mês | 🟡 |
| Renovação do trial | Gratuita (até 6 meses por vez) | ✅/🟡 |
| Edições comerciais (relato 2022) | US$ 25 mil / 50 mil por ano | 🟡 |
| App próprio (relato) | US$ 5 mil / 2 mil por ano | 🟡 |
| Excedente (Flagship, relato) | US$ 3,15/M chamadas · US$ 1,24/M mensagens | 🟡 |

**Leitura honesta:** o trial **não suporta nem um piloto com 3 casas** (10 dispositivos controláveis no total). Servirá para provar a tecnologia em **uma** casa. O custo da nuvem é o **Portão 1** do projeto.

## 8. Alexa

### 8.1 O que Alexa é (e não é) nesta arquitetura

- ✅ **Interface de voz paralela**, via skill **Smart Life** da Tuya: o cliente a ativa no app Alexa e os dispositivos Tuya aparecem; "Alexa, acende a luz da sala". **Zero código nosso**, funciona mesmo com o nosso servidor fora.
- 🟡 Cenas/dispositivos do Smart Life aparecem na Alexa; sensores de contato/movimento podem ser **gatilhos de rotinas da Alexa** (testar no S5). Útil para automações mínimas **sem nosso backend**.
- ⛔ **Backend ou fonte de eventos.** Não há API oficial para receber eventos de dispositivos de outras skills (A5, 🟡). Não use APIs não oficiais (ex.: Alexa Media Player): quebram e violam termos.
- ⛔ **Motor de automações críticas.**

### 8.2 Skill própria (Fase 3) — quando e como

**Quando vale:** (a) vender **voz para as cenas da plataforma** ("Alexa, cheguei"); (b) **obrigatória** se migrarmos para dispositivos locais fora da Tuya Cloud — aí a skill Smart Life deixa de enxergar esses dispositivos.

**O que exige** 🟡 *(página oficial bloqueada; confirmar):*

| Peça | Detalhe |
|---|---|
| Idioma | **pt-BR é suportado** (A1) |
| Endpoint | HTTPS ou Lambda em us-east-1 (A1) |
| Account linking | **Servidor OAuth 2.0 (authorization code)** — implementação própria, ~1–2 semanas |
| Descoberta e controle | Interfaces `PowerController`, `BrightnessController`, `ThermostatController`, `LockController`, `ContactSensor`, `MotionSensor`, `TemperatureSensor`, `SceneController`, `EndpointHealth` |
| Eventos proativos | `AcceptGrant` + `ChangeReport` com tokens LWA por usuário |
| Fechadura | Exige confirmação por **código de voz**; disponibilidade em pt-BR 🔬 |
| Publicação | Certificação (testes, credenciais de teste, UX em pt-BR); beta até 500 usuários / 90 dias 🟡; **prazo não confirmado** |
| Esforço | ≈ 4–6 pessoa-semanas + certificação |

### 8.3 Roteiro de instalação da voz (MVP)

1. Cliente instala o app **Alexa** e (se ainda não tiver) o dispositivo Echo.
2. *Skills → Smart Life → Ativar → login com a conta Smart Life → Descobrir dispositivos*.
3. Nomes pt-BR curtos e sem ambiguidade (`Luz da sala`, `Ar do quarto`); agrupar por **ambiente** no app Alexa.
4. Testar 5 frases-padrão e entregar um cartão de comandos.
5. **Custo opcional:** Echo Dot 5ª geração R$ 354–429; Echo Pop mais barato 🟡.
