# 04 · Integração Tuya e Alexa

Selos: ✅ confirmado · 🟡 provável · 🔬 necessita teste · ⛔ não recomendado ([01](01-evidencias-e-pesquisa.md)).

## 1. Cinco caminhos de acesso à Tuya

| Rota | O que é | Custo oficial | Quando usar | Selo |
|---|---|---|---|---|
| **A. Projeto de nuvem *Smart Home* (Open API + Message Service)** | Projeto no console; vínculo da conta **Smart Life** do cliente por QR (*Link Tuya App Account*, até 2 projetos por conta); **IoT Core** + **Message Service** | **Trial grátis, só para depuração (uso comercial proibido)**. Comercial: **Flagship US$ 25 mil/ano** (Corporate US$ 50 mil) | **POC na sua casa.** Escala comercial só após o Portão 1 | Técnica ✅ · termos ✅ (restritivos) |
| **B. App próprio** (*Self-Developed Smart Life App*, App SDK) | App com a sua marca: contas, pareamento e controle no SDK; dispositivos ficam na conta do **seu** app | **US$ 5 mil (1º ano) / US$ 2 mil (renovação)**, usuários ilimitados; a cota do SDK **não** cobre a Open API (essa exige IoT Core) | Melhor plug-and-play; Arquitetura D ([03](03-arquitetura-e-stack.md)) | Preço ✅ · integração 🔬 |
| **C. Device Sharing (QR + User Code)** | Fluxo da integração oficial da Tuya **para o Home Assistant** | — | — | ⛔ |
| **D. Controle local (LAN)** | `tinytuya`/`tuyapi` (MIT); 1 conexão TCP por dispositivo; sem dispositivos a bateria; **a `local_key` vem da conta de nuvem** | Depende de A ou B para obter a chave | Edge Box; fallback sem internet | ✅ |
| **E. Zigbee aberto** | Dispositivos Zigbee (inclusive de marca Tuya) num coordenador seu, com `zigbee-herdsman` (MIT) | **Sem nuvem Tuya** | Edge Box; elimina a taxa | Licenças ✅ · modelo a modelo 🔬 |

> **Decisão:** POC na **Rota A** (Trial, sua casa), com o código atrás do `ProviderAdapter`. No **Portão 1**, escolher entre **A com Flagship/plano negociado**, **B** (se o produto for centrado em app) e **E (+D)** (Edge). Detalhe importante: a Rota **D não elimina a relação com a Tuya** (só a dependência em tempo de execução, porque a `local_key` sai da nuvem); **só a E é independente**.

## 2. Passo a passo da Rota A (POC)

1. **Console Tuya**: conta de desenvolvedor e **projeto do tipo *Smart Home*** ("vincule dispositivos ao seu app SmartLife… e chame a OpenAPI" ✅). Escolha o **data center da conta do app**. **Brasil:** *Eastern America* para **apps** registrados desde 2025-11-25 (REST `openapi-ueaz.tuyaus.com`, Pulsar `mqe-ueaz.tuyaus.com`); apps anteriores continuam no *Western America* ✅. A doc é escrita para apps OEM: **para o app Smart Life, qual data center vale é 🔬 (S1)**. Se o dispositivo não aparece na lista, **troque o data center** ✅. Hospede o Core **nas Américas** (a Tuya veda chamadas de outra região; erro 2007 ✅).
2. **Serviços**: assinar o **IoT Core (Trial)** e habilitar o **Message Service**; autorizar o projeto em **Authorization Token Management**, **Smart Home Basic Service**, **IR Control Hub Open Service** e, para testar fechadura, **Smart Lock Open APIs** ✅. Copiar **Access ID** e **Access Secret**; opcional: **lista de IPs permitidos** do projeto ✅.
3. **Dispositivos**: parear tudo no app **Smart Life** com nomes `Ambiente · Função` (ex.: `Sala · Luz principal`). Ver [07](07-plug-and-play-e-instalacao.md).
4. **Vínculo**: *Devices → Link Tuya App Account → Add App Account*, escanear o QR com o Smart Life e tocar em *Confirm login* ✅. **É manual e feito no console, por conta** — o principal gargalo de plug-and-play desta rota. Cada conta de app pode estar em **no máximo 2 projetos** ✅.
5. **Importação**: listar os dispositivos (`GET /v1.0/iot-03/devices`) e ler `…/{id}/specification` (tipos, mín/máx/escala/enum) ✅.
6. **Eventos**: `PulsarConsumer` no tópico `event` (produção), `encryption: 'ecb'` (padrão ✅). Trate o `protocol` da mensagem (**4** status, **20** online/offline, **1000/1001** IoT Core) e **não ative os dois conjuntos de protocolos** (duplica mensagens ✅).
7. **Comandos**: duas rotas candidatas — `POST /v1.0/iot-03/devices/{id}/commands` e `POST /v2.0/cloud/thing/{id}/shadow/properties/issue` — **testar no S1** (🔬, [01](01-evidencias-e-pesquisa.md) T27); rotas de IR ✅.
8. **Validar**: spikes S1, S1b, S2, S3 ([01](01-evidencias-e-pesquisa.md) §6).

### Código (validado contra o SDK oficial)

`poc/tuya-core` — 27 testes; assinatura, token/refresh, comandos, IR e consumidor Pulsar:

```ts
import { TuyaClient, PulsarConsumer, TUYA_API_ENDPOINTS, TUYA_PULSAR_ENDPOINTS } from './src/index.ts';

const tuya = new TuyaClient({
  endpoint: TUYA_API_ENDPOINTS.ueaz,         // Brasil: Eastern America (🔬 confirmar no vínculo; pode ser `us`)
  clientId: process.env.TUYA_CLIENT_ID!,
  secret: process.env.TUYA_SECRET!,           // nunca no frontend
});

await tuya.sendCommands(deviceId, [{ code: 'switch_led', value: true }]);          // luz (rota a confirmar no S1)
await tuya.acScene(irHubId, acRemoteId, { power: 1, mode: 1, temp: 24, wind: 1 });  // ar-condicionado por IR

new PulsarConsumer({
  accessId: process.env.TUYA_CLIENT_ID!,
  secret: process.env.TUYA_SECRET!,
  wsEndpoint: TUYA_PULSAR_ENDPOINTS.ueaz,     // 8285 inferido do padrão (🔬)
  onEvent: (evt, meta) => normalizeAndStore(evt, meta.protocol),   // {devId, status:[{code,value,t}]}
  onError: (err) => log.error(err),
}).start();
```

Diferenças deliberadas em relação ao SDK Python: **verificação TLS ligada**, ACK sempre (sem laço de reentrega), reconexão com backoff, *single-flight* de token, corpo assinado = corpo enviado, nova tentativa **única** nos erros de token **1010/1011/1012** ✅.

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

**Categorias de produto** (`category`). Confirmadas ✅ pela doc da Tuya sobre a integração do HA: `kt` ar-condicionado · `kg` interruptor · `cz` tomada · `wsdcg` temperatura/umidade · `mcs` sensor de porta/janela · `pir` infravermelho passivo (movimento) · `hps` presença humana · `ywbj` fumaça · `zndb` medidor de energia · `dj` luz · `cl`/`clkg` cortina · `tgkg`/`tgq` dimmer · `sgbj` alarme sonoro/visual · `ykq` controle remoto. **Fora dessa lista** (existem no código do HA, descrições 🟡): `wnykq` hub IR · `ms`/`msp`/`jtmspro` fechaduras · `wxkg`/`cjkg` botões e cenas — **o conector oficial do HA não suporta fechaduras nem hub IR** ✅, sinal de que são categorias à parte.

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
- **Cenas no nosso motor**: ações paralelas por passo, `delay_ms`, resultado por ação, falha parcial reportada. Cenas nativas da Tuya continuam existindo para a Alexa/Smart Life e **não** são nossa fonte de verdade (evita duplicidade). **Exceção a avaliar:** como o envio de propriedades é limitado a **4/s por projeto** e o disparo de cena nativa a 10/s ✅, cenas só com dispositivos Tuya podem usar o disparo nativo (1 chamada = N ações) 🔬 — ver [03](03-arquitetura-e-stack.md) §5.1.
- **Automações simples** no servidor: gatilho (estado/horário/pôr do sol) + condição (janela de horário, `home.mode`) + ação (cena/comando/alerta) + `cooldown`. Detalhes em [08](08-mvp-custos-negocio-riscos.md).
- **"Ninguém em casa"**: no MVP é um **modo da casa** (`home/away/night/vacation`) acionado por cenas (*Saí*, *Cheguei*, *Boa noite*), não por geofence (iOS em PWA não é confiável 🔬).

## 6. Fechadura (MVP 2, com teste prévio por modelo)

- **Serviço de API separado:** *Smart Lock Open APIs* ✅ (preço e condições exigem login no console; perguntar no e-mail, [01](01-evidencias-e-pesquisa.md) §7).
- **A fechadura precisa suportar abertura remota por nuvem:** o FAQ oficial descreve o mecanismo de **chave em nuvem (DP 49/50)**, que o firmware da fechadura tem de implementar ✅. Nem todo modelo faz isso.
- Rotas de abertura remota: `password-ticket` → `password-free/open-door` 🟡 (resumo de busca).
- O conector oficial do HA **não suporta fechaduras** ✅.
- **Teste o modelo exato antes de comprar lote** (S4).
- Mercado BR: fechaduras com app Tuya/Smart Life de **R$ 318 a R$ 1.780** 🟡 (ex.: Aliança Titan Ultra com Wi-Fi).
- Salvaguardas (obrigatórias): `can_unlock`, PIN/biometria no cliente, *rate limit*, notificação a todos os donos, **sem reenvio automático**, **nenhuma automação abre por padrão**, falha segura, chave física sempre disponível, termo de responsabilidade e atenção a **imóvel alugado** (troca de cilindro exige anuência do proprietário).

## 7. Limites, custos e termos da Tuya (fonte oficial)

| Item | Valor | Selo |
|---|---|---|
| **Trial** | 50 dispositivos / 10 controláveis; 26 mil chamadas e 68 mil mensagens/mês; sem excedente; **uso comercial proibido** | ✅ |
| **Flagship** (12 meses) | **US$ 25.000/ano**; 224 M chamadas + 568 M mensagens/mês; 75 mil dispositivos / 30 mil controláveis; 7 data centers | ✅ |
| **Corporate** (12 meses) | **US$ 50.000/ano**; 426 M + 1 bi; 200 mil / 75 mil | ✅ |
| Excedente (Flagship) | US$ 3,15/M chamadas · US$ 1,24/M mensagens | ✅ |
| **App próprio** (Official) | **US$ 5.000 (1º ano) · US$ 2.000 (renovação)**; usuários ilimitados; cota do SDK não cobre a Open API | ✅ |
| **Limites por projeto** | enviar propriedades **4/s**; ler propriedades 50/s; ler estado 5/s; disparar cena 10/s | ✅ |
| **Contrato** | Licença **não sublicenciável**; veda "uso comercial ou distribuição do Serviço" (3-ix) e "uso em benefício de terceiros" (3-xi) **salvo o permitido pelo serviço ou por ordem de serviço assinada**; suspensão **sem aviso** em vários casos; **responsabilidade da Tuya limitada a US$ 5.000**; foro da Califórnia | ✅ |
| Privacidade | O desenvolvedor responde pela conformidade (LGPD); a Tuya pode usar dados processados para melhorar serviços | ✅ |

**Códigos de erro para tratar no adaptador** ✅: **1010** token expirado · **1011** token inválido · **1012** status do token inválido (renovar e repetir uma vez) · **1106** sem permissão · **1110** limite de concorrência · **1199** requisições frequentes (*backoff*) · **2001** dispositivo offline · **2007** IP de outra região · **2008** comando/valor não suportado · **28841004** cota do trial esgotada · **28841104** cota da API esgotada · **28841105** projeto sem autorização · **28841101** API não assinada.

**Leitura honesta:**

- O Trial serve para **provar a tecnologia na sua casa**. Com 10 dispositivos "controláveis", cobre uma casa pequena; **nenhum cliente, nem piloto pago, pode usá-lo**.
- O contrato foi escrito para **desenvolvedores e marcas**, não para integradores que atendem terceiros: a **ordem de serviço escrita** é parte do Portão 1.
- A responsabilidade da Tuya é limitada a US$ 5 mil e ela pode suspender o projeto sem aviso: **o plano B (D/E) não é opcional para um produto de segurança e conforto**.

## 8. Alexa

> Desde 2026 a Amazon chama as *skills* de casa inteligente de **add-ons** (integrações existentes continuam; [01](01-evidencias-e-pesquisa.md) A2).

### 8.1 O que Alexa é (e não é) nesta arquitetura

- ✅ **Interface de voz paralela**, via skill **Smart Life** da Tuya (🟡 no Brasil, A5): o cliente a ativa no app Alexa e os dispositivos Tuya aparecem; "Alexa, acende a luz da sala". **Zero código nosso**, funciona mesmo com o nosso servidor fora.
- 🟡 Cenas/dispositivos do Smart Life aparecem na Alexa; sensores de contato/movimento podem ser **gatilhos de rotinas da Alexa** (testar no S5). Útil para automações mínimas **sem nosso backend**.
- ⚠️ **Se os dispositivos estiverem num app próprio (Rota B)**, a skill Smart Life **não os vê**: é preciso o serviço *Smart Voice* da Tuya (preço a pedir) ou um add-on próprio.
- ⛔ **Backend ou fonte de eventos.** Não há API oficial para receber eventos de dispositivos de outras skills (A6, 🟡). Não use APIs não oficiais (ex.: Alexa Media Player): quebram e violam termos.
- ⛔ **Motor de automações críticas.**

### 8.2 Add-on próprio (Fase 3): quando e como

**Quando vale:** (a) vender **voz para as cenas da plataforma** ("Alexa, cheguei"); (b) **obrigatório** se migrarmos para dispositivos fora da Tuya Cloud (Rota E) ou para app próprio: a skill Smart Life deixa de enxergá-los.

**O que exige** (✅ salvo indicação):

| Peça | Detalhe |
|---|---|
| Idioma e região | **Português (BR) suportado**; função **Lambda em US East (N. Virginia)**; endpoint Alexa **América do Norte**; eventos em `https://api.amazonalexa.com/v3` ✅ (A1) |
| Account linking | **OAuth 2.0** próprio (authorization code); as **URLs de redirecionamento da Alexa** de cada região Lambda devem ser liberadas no seu provedor OAuth ✅. Estimativa: 1–2 semanas |
| Descoberta e controle | Interfaces listadas na doc: `BrightnessController`, `ColorTemperatureController`, `ContactSensor`, `TemperatureSensor`, `ThermostatController`, `LockController`, `EndpointHealth`… (confirmar `PowerController`, `MotionSensor`, `SceneController` na referência) |
| Eventos proativos | `AcceptGrant` + `ChangeReport` ao *event gateway* com tokens por usuário ✅ (existência) |
| Fechadura | Exige confirmação por **código de voz**; disponibilidade em pt-BR 🔬 |
| Certificação | *Account linking* testado; **credenciais de teste por idioma**; **≥ 1 dispositivo descobrível e online 24/7 durante o teste**; **política de privacidade e termos de uso** acessíveis em iOS/Android/desktop; conteúdo da loja em cada idioma (descrição, frases de exemplo, ícones, palavras-chave) ✅. **Prazo não publicado** 🔬 |
| Beta | A ferramenta existe (testadores pelo e-mail da conta Alexa) ✅; **os limites numéricos não constam na doc atual** ❓ |
| Esforço | ≈ 4–6 pessoa-semanas + certificação |

### 8.3 Roteiro de instalação da voz (MVP)

1. Cliente instala o app **Alexa** e (se ainda não tiver) o dispositivo Echo.
2. *Skills → Smart Life → Ativar → login com a conta Smart Life → Descobrir dispositivos*.
3. Nomes pt-BR curtos e sem ambiguidade (`Luz da sala`, `Ar do quarto`); agrupar por **ambiente** no app Alexa.
4. Testar 5 frases-padrão e entregar um cartão de comandos.
5. **Custo opcional:** Echo Dot 5ª geração R$ 354–429; Echo Pop mais barato 🟡.
