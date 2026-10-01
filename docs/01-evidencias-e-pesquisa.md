# 01 · Evidências e pesquisa

Data: **2026-10-01** · **Atualizado após a liberação de rede**: li as páginas oficiais da Tuya, da Amazon (Alexa) e do Supabase. Este documento separa o que foi **verificado** do que é **provável** ou **precisa de teste**.

| Selo | Significado |
|---|---|
| ✅ **Confirmado** | Verificado em fonte primária (página oficial lida, código-fonte que baixei e li, ou teste que executei). |
| 🟡 **Provável** | Veio de resumo de busca, fonte secundária ou conhecimento prévio; coerente, mas **não li a página oficial**. |
| 🔬 **Necessita teste** | Só se resolve com dispositivo, conta ou console reais (ver spikes, seção 5). |
| ⛔ **Não recomendado** | Possível, mas inadequado para um produto comercial. |

## 1. Acesso às fontes

Os 10 hosts que estavam bloqueados **agora respondem**: `developer.tuya.com`, `support.tuya.com`, `tuya.com`, `www.tuya.com`, `developer.amazon.com`, `supabase.com`, `www.home-assistant.io`, `community.home-assistant.io`, `apis.io` e `lgrsv.github.io`. Particularidades: `support.tuya.com` entra em laço de redirecionamento **sem cookie de idioma** (funciona com cookie); `community.home-assistant.io` devolve 403 ao `curl` simples, mas abre pelo leitor web.

**Ainda não verificado:**

- **Nenhuma chamada real à Tuya** foi feita (não há credenciais).
- **Preço e termos das APIs verticais** *Smart Lock Open APIs* e *IR Control Hub Open Service* (as páginas de cobrança por serviço exigem login).
- **Prazo de certificação** de um add-on Alexa (a doc não publica).
- A demo da referência foi **renderizada** em Chromium com renderização por software (SwiftShader) para observar a UX; por isso o visual ficou no nível de qualidade `min`. A análise principal continua **pelo código-fonte** ([02](02-referencia-igreja-3d.md)).

## 2. Evidências: Tuya

| # | Afirmação | Selo | Fonte (data) |
|---|---|---|---|
| T1 | **Trial** do IoT Core: **50 dispositivos** e **10 controláveis** (controlável = dispositivo ao qual você envia comandos; cada um consome 1 unidade); 1 data center; validade de 1 mês | ✅ | Página *Pricing* (2026-07-28); loja do IoT Core; Help Center |
| T2 | Trial: **26 mil chamadas de API e 68 mil mensagens por mês**, **sem excedente** (suspende até virar o mês) | ✅ | *Pricing* (2026-07-28) |
| T3 | **"O Trial só se aplica a desenvolvedores individuais ou a depuração. Uso comercial é proibido."** | ✅ | *Pricing* (2026-07-28) |
| T4 | Ao expirar o trial, **as APIs deixam de funcionar e as mensagens deixam de chegar**; para continuar é preciso a **Flagship** | ✅ | Help Center (2024-04-17) |
| T5 | **Flagship** (12 meses): 224 M chamadas + 568 M mensagens/mês · **75 mil** dispositivos / **30 mil** controláveis · 7 data centers · logs de 72 h. **Corporate**: 426 M + 1 bi · 200 mil / 75 mil · 168 h | ✅ | *Pricing* (2026-07-28) |
| T6 | **Preço: Flagship US$ 25.000/ano (¥ 150.000) · Corporate US$ 50.000/ano (¥ 300.000)**, contrato de 12 meses, pré-pago, sem reembolso | ✅ | Loja do IoT Core (dados da página; escala ÷100 calibrada com o preço exibido do App SDK, ¥ 33.500) |
| T7 | Excedente (fora da China): Flagship **US$ 3,15/M chamadas** e **US$ 1,24/M mensagens**; Corporate US$ 2,97 e US$ 1,17. Os exemplos oficiais citam um *allowance* de US$ 1.500/mês na Flagship | ✅ | *Pricing* |
| T8 | **App próprio** (*Self-Developed Smart Life App*, edição Official): **US$ 5.000 no 1º ano (¥ 33.500) e US$ 2.000 na renovação (¥ 13.000)**; usuários ilimitados; 100 M chamadas/mês **do SDK**; domínio próprio. Edição de desenvolvimento: grátis, ≤ 100 usuários, 100 mil chamadas/mês, "só para desenvolvimento e depuração" | ✅ | Loja Tuya (App SDK) |
| T9 | A cota do App SDK **não se aplica** às chamadas da Open API de nuvem; para estas é preciso o IoT Core | ✅ | Loja Tuya (App SDK) |
| T10 | A Tuya separa projetos **Smart Home** (apps OEM ou feitos com o Smart App SDK; vínculo de contas) e **Custom Development** (ativos/B2B) | ✅ | *Cloud Integration Solutions* (2024-06-19) |
| T11 | Vínculo de conta Smart Life por QR (*Link Tuya App Account*); **cada conta só em até 2 projetos**; se o dispositivo não aparece, trocar o data center | ✅ | *Link Devices* (2025-06-23) |
| T12 | **Contrato**: licença **não sublicenciável**; veda "uso comercial ou distribuição do Serviço" (cl. 3-ix) e "uso em benefício de terceiros" (3-xi), **salvo o permitido pelas features do serviço ou por ordem de serviço assinada**; a Tuya pode suspender ou restringir **sem aviso prévio** em vários casos; responsabilidade da Tuya **limitada a US$ 5.000**; foro da Califórnia | ✅ | *Tuya IoT Development Platform Service Agreement* (2023-03-01) |
| T13 | O desenvolvedor responde pela **conformidade de privacidade**; a Tuya pode usar dados processados para melhorar os serviços | ✅ | *Common Protocol for Cloud Development* |
| T14 | O fluxo "QR + User Code" é a **"integração oficial da Tuya para o Home Assistant"** (HA Core ≥ 2024.2.0); no código, `client_id = HA_3y9q4ak7g4ephrvke`, `schema = haauthorize`, rotas `/v1.0/m/life/home-assistant/qrcode/…` e `/ha/…` | ✅ | Doc da Tuya (2025-03-03) + código do HA e `tuya-device-sharing-sdk` |
| T15 | Usar o *Device Sharing* como base de produto comercial | ⛔ | Consequência de T14 |
| T16 | Assinatura da Open API (`HMAC-SHA256`), token em `GET /v1.0/token?grant_type=1`, refresh em `/v1.0/token/{refresh}` | ✅ | SDKs Python e Node; **5 vetores idênticos** no meu TypeScript |
| T17 | **Message Service**: Pulsar sobre WebSocket; assinatura padrão `{AccessId}-sub`; canais PROD (`event`) e TEST (exige escolher dispositivos de teste); endpoints por data center (ver T21) | ✅ | Docs do Message Service (2026-03-17, 2025-09-30) |
| T18 | Mensagem em **duas camadas**: `payload` (base64) → `{data, protocol, pv, t, sign}` → `data` cifrado com **AES/ECB (padrão)**, chave = 16 caracteres do meio do Access Secret; **AES/GCM é opcional**, ativado por você no console; verificação `sign` (MD5) é opcional | ✅ | *Data Signature and Decryption* (2025-06-25); meu código e testes batem com o SDK |
| T19 | Protocolos: **4** = status de dispositivo (legado), **20** = online/offline (legado), **1000/1001** = IoT Core (dados e gestão); configurar os dois conjuntos **pode duplicar mensagens** | ✅ | *Message Types* (2024-12-30) |
| T20 | O SDK Python da Tuya **desativa a verificação TLS** (`ssl.CERT_NONE`) | ✅ | Lido em `openpulsar.py` |
| T21 | **Brasil → Eastern America** (Virginia, Google Cloud) para **apps registrados desde 2025-11-25**; antes era Western America e **apps existentes não mudam**. REST: `openapi-ueaz.tuyaus.com`; Pulsar: `mqe-ueaz.tuyaus.com` | ✅ doc (escrita para apps OEM) · regra exata para o app **Smart Life** 🔬 | *App Accounts and Data Centers* (2026-08-12), *Data Center* (2026-02-26), *Integrate with Message Service* |
| T22 | Chamadas vindas de **outro data center/região são proibidas** (erro 2007 "IP cross-region") | ✅ | *Global Error Codes*; wiki oficial do HA |
| T23 | **Limites por projeto** (APIs v2.0): enviar propriedades **4/s** · enviar ações 4/s · ler propriedades 50/s · estado 5/s · disparar cena 10/s | ✅ | *Limits on API Request Frequency* (2023-06-25) |
| T24 | Erros: **1010 token expirado · 1011 token inválido · 1012 status do token inválido** · 1004 assinatura · 1106 sem permissão · 1110 limite de concorrência · 1199 requisições frequentes · 2001 dispositivo offline · 2008 comando não suportado · 28841004 cota do trial esgotada · 28841104 cota da API esgotada · 28841105 projeto sem autorização | ✅ | *Global Error Codes* (2024-07-22) |
| T25 | Serviços de API a autorizar: **IoT Core**, **Authorization Token Management**, **Smart Home Basic Service**, **IR Control Hub Open Service** (infravermelho), **Smart Lock Open APIs** (fechaduras) e o **Message Service** | ✅ | *Smart Home APIs*, *Manage Projects* |
| T26 | Rotas de leitura `/v1.0/iot-03/devices/{id}/status`, `/specification`, `/functions` e a lista de dispositivos | ✅ | SDK Node oficial 2.1.2 |
| T27 | **Comandos**: a rota `POST /v1.0/iot-03/devices/{id}/commands` não aparece em nenhuma fonte que li (a página "Device Control" é do PaaS de iluminação; o SDK Node só tem `GET …/commands`). A rota `POST /v2.0/cloud/thing/{id}/shadow/properties/issue` consta na tabela oficial de limites | 🔬 | Testar as duas no S1 |
| T28 | **IR**: `…/infrareds/{ir}/air-conditioners/{ac}/command` e `/scenes/command`, `/remotes/{id}/keys`, `/raw/command` (e o serviço *IR Control Hub Open Service*) | ✅ | Código da integração `tuya-smart-ir-ac` + lista de serviços |
| T29 | **Fechadura**: serviço vertical separado (*Smart Lock Open APIs*); a abertura remota exige que a fechadura implemente o mecanismo de **chave em nuvem (DP 49/50)**; rotas `password-ticket` e `open-door` | ✅ serviço e DP · 🟡 rotas | Doc *Wi-Fi Lock FAQs*; resumo de busca |
| T30 | O conector oficial do HA **não lista fechaduras nem hub IR** entre as categorias suportadas | ✅ | Doc da Tuya sobre o HA (2025-03-03) |
| T31 | Controle **local** (LAN): protocolos 3.1–3.5, **1 conexão TCP por dispositivo**, dispositivos a bateria não funcionam local, e a **`local_key` vem da conta de nuvem** (o *wizard* exige projeto IoT) | ✅ | README do `tinytuya` |
| T32 | Contatos comerciais: **vip@tuya.com** ("Business Cooperation"), service@tuya.com, +1 844-672-5646 | ✅ | Rodapé do site |

## 3. Evidências: Alexa (Amazon)

| # | Afirmação | Selo | Fonte |
|---|---|---|---|
| A1 | **Português (BR) é suportado**; região Lambda **US East (N. Virginia)**; endpoint Alexa **América do Norte**; eventos em `https://api.amazonalexa.com/v3` | ✅ | *Develop Smart Home Add-ons for Multiple Languages* |
| A2 | "Smart home **skills** agora se chamam **add-ons**" (integrações existentes continuam) | ✅ | Idem |
| A3 | Certificação: *account linking* OAuth testado; **credenciais de teste por idioma**; ≥ 1 dispositivo descobrível e **online 24/7 durante o teste**; links de política de privacidade e termos de uso; conteúdo por idioma; WWA é outro processo. **Prazo não publicado** | ✅ · prazo 🔬 | *Smart Home Certification Guide* |
| A4 | Beta: a ferramenta existe (testadores identificados pelo e-mail da conta Alexa); **os limites "500 testadores / 90 dias" que li em resumo de busca NÃO constam na doc atual** | ✅ existe · limites ❓ | Doc de beta |
| A5 | A skill **Smart Life** da Tuya funciona no Brasil | 🟡 | Resultado de busca; testar no S5 |
| A6 | Não há API oficial para receber eventos de dispositivos de *outras* skills | 🟡 | Conhecimento prévio |

## 4. Evidências: concorrência, mercado, stack

| # | Afirmação | Selo | Fonte |
|---|---|---|---|
| C1 | **SmartThings Map View 3D**: planta por foto, endereço, desenho ou LiDAR de aspirador Samsung vira layout 3D com dispositivos; em Android, iOS e **TVs Samsung** | ✅ | Samsung Newsroom |
| C2 | Anatel: Wi-Fi/Bluetooth vendidos no Brasil exigem **homologação** (Res. 242/2000) | 🟡 | Resumos de busca; validar com especialista |
| C3 | INMETRO para plugues/tomadas inteligentes | 🔬 | Não confirmado |
| C4 | Preços de varejo BR (2026): lâmpada R$ 26–50 · hub IR R$ 40–100 · sensor de porta R$ 80–112 · tomada com medidor R$ 35–130 · Echo Dot R$ 354–429 · fechadura Wi-Fi R$ 318–1.780 | 🟡 | Anúncios |
| W1 | Versões (npm, 2026-10-01): `three` 0.186.1 · `@react-three/fiber` 9.8.1 · `@react-three/drei` 10.7.9 · `babylonjs` 9.29.0 · `vite` 8.3.2 · `react` 19.3.0 · `@supabase/supabase-js` 2.117.2 · `fastify` 5.12.5 · `@capacitor/core` 8.5.2 · `workbox-build` 7.4.1 · `@gltf-transform/cli` 4.5.1 · `ws` 8.22.0 | ✅ | `npm view` |
| W2 | Licenças MIT (three, R3F, drei, supabase-js, ws, tuyapi, tuya-connector-nodejs, `zigbee-herdsman` e `-converters`); Apache-2.0 (Babylon, matter.js, pulsar-client) | ✅ | `npm view … license` |
| W3 | `extras` do glTF viram `userData` nos nós do Three.js; R3F 9.8.1 tem `frameloop="demand"` e `invalidate()` | ✅ | Código do `GLTFLoader`; tipos do R3F |
| W4 | WebGPU nos navegadores principais; TVs Samsung com Chromium M94/M108; webOS e desempenho 3D | 🟡 / 🔬 | Resumos; testar em TV real |
| W5 | **Supabase Pro a partir de US$ 25/mês**: 100 mil MAU, 8 GB, 250 GB de egress, 100 GB de storage, backups de 7 dias. **Free**: 50 mil MAU, 500 MB, pausa após 1 semana, 2 projetos. Team a partir de US$ 599 | ✅ | Página de preços |
| W6 | **Região São Paulo (`sa-east-1`)** disponível | ✅ | Docs de regiões |
| W7 | **Realtime**: Pro **500 conexões simultâneas** e **500 mensagens/s**; sem *spend cap* 10.000 e 2.500 msg/s; Free 200 e 100 | ✅ | Docs de limites do Realtime |

## 5. Verificações que eu mesmo executei

| O quê | Resultado |
|---|---|
| Assinatura Tuya (TS) vs. SDK Python oficial, 5 casos | ✅ idênticas |
| Senha, URL e decriptação do Pulsar (TS) vs. SDK Python oficial | ✅ idênticas |
| Formato de 2 camadas e `protocol` das mensagens | ✅ conforme a doc oficial |
| Consumidor Pulsar contra servidor WebSocket simulado: handshake, evento, ACK, reconexão | ✅ |
| Cliente Tuya com `fetch` falso: token, refresh, corpo assinado = corpo enviado, erros 1010/1011/1012 com nova tentativa única, 1106 sem nova tentativa | ✅ **27 testes passam** (`poc/tuya-core`) |
| Schema multi-tenant em **PostgreSQL 16 real** | ✅ **50 asserções passam** (`database/tests/run.sh`) |

> **Correções que as fontes oficiais impuseram ao meu código:** o código `1010` significa *token expirado* (eu o tratava como "inválido"); `1011` e `1012` também são erros de token; o `protocol` da mensagem precisa chegar ao *handler*; e o Brasil usa o endpoint **Eastern America** (`ueaz`), que não estava na lista.

## 6. Spikes de validação (1 semana, antes de gastar com o MVP)

| Spike | Como | Saída esperada |
|---|---|---|
| **S1 · Tuya ponta a ponta** | Conta e projeto **Smart Home**, **data center correto**, assinar IoT Core (trial) e Message Service, autorizar os serviços (T25), vincular uma conta Smart Life por QR, listar dispositivos, ler `specification`, **testar as duas rotas de comando (T27)**, receber o evento por Pulsar com `poc/tuya-core` | Lâmpada comandada e evento em < 2 s. Resolve T21 (Smart Life no Brasil), T27 e o endpoint WebSocket do `ueaz` |
| **S1b · Limites** | Disparar 10–20 comandos em paralelo e medir *throttling* (1110/1199); ver quanto o vínculo consome dos 10 "controláveis" | Taxa real de comandos por projeto |
| **S2 · IR e ar-condicionado** | Hub IR + TV + split pelas rotas de IR | Ligar o ar a 24 °C e trocar de canal por API |
| **S3 · Sensores e energia** | Porta, movimento, tomada com medidor: **mensagens/dia reais** e polaridade de `doorcontact_state` | Tabela real de DPs, escalas e volume |
| **S4 · Fechadura (opcional)** | Modelo candidato: abertura remota por API (DP 49/50) e log de eventos | Sim/não por modelo, com requisitos |
| **S5 · Alexa nativa** | Skill Smart Life: luzes, cenas, sensores como gatilho de rotina, voz em pt-BR | Roteiro validado + limites reais |
| **S6 · 3D em 3 dispositivos** | GLB de teste com 10 objetos em Android médio, iPhone, tablet barato e TV | FPS, memória, decisão sobre o modo lista |
| **S7 · Resposta da Tuya** | Enviar o e-mail abaixo | Proposta escrita de custo e termos |

## 7. E-mail para a Tuya (modelo)

Enviar para **vip@tuya.com** (*Business Cooperation*), com cópia para service@tuya.com.

> Assunto: Licenciamento comercial — integrador de automação residencial no Brasil
>
> Somos integradores de automação residencial no Brasil. Instalaremos, em apartamentos, dispositivos Tuya/Smart Life (iluminação, infravermelho, sensores, tomadas com medidor e, futuramente, fechaduras) e ofereceremos ao cliente final um painel próprio (web/app) que lê estado e envia comandos via Open API e Message Service. Já lemos a página *Pricing* (Trial só para depuração, Flagship US$ 25 mil/ano) e o *Service Agreement* (licença não sublicenciável; cl. 3-ix e 3-xi). Precisamos de respostas **por escrito**:
>
> 1. O modelo "um projeto nosso atendendo N residências de clientes distintos" é **permitido** pelo contrato? Podemos obter uma **ordem de serviço** que autorize expressamente o uso em benefício de terceiros (nossos clientes)?
> 2. Existe plano **para startups ou pilotos** (até ~50 residências) com custo proporcional, em vez dos US$ 25 mil/ano da Flagship? O que as exceções "special needs" do *Pricing* cobrem?
> 3. Para esse caso, o caminho correto é **projeto Smart Home com vínculo de contas Smart Life** ou **app próprio (App SDK / OEM)**? No segundo caso, o IoT Core Flagship continua obrigatório para a Open API? A cota do App SDK (100 M) só cobre chamadas do SDK?
> 4. **Limites por projeto:** o envio de propriedades é limitado a 4/s. Qual o caminho recomendado para cenas com vários dispositivos em muitas casas simultâneas (grupos, cenas nativas, limite maior)?
> 5. **Brasil:** contas Smart Life existentes estão no Eastern America ou no Western America? Há restrição de onde nosso servidor pode ficar (erro 2007)?
> 6. **Fechaduras e IR:** preço e condições dos serviços *Smart Lock Open APIs* e *IR Control Hub Open Service*; quais fechaduras suportam abertura remota por API.
> 7. **Alexa:** para dispositivos em app próprio, como funciona o serviço *Smart Voice* (preço e prazo)?
> 8. Tratamento de dados pessoais (LGPD) e localização dos dados.
>
> Obrigado.

## 8. Critério de decisão (Portão 1)

| Resposta da Tuya | Decisão |
|---|---|
| Custo variável por casa **≤ ~R$ 10/mês** (ou taxa fixa que dilua nisso) **e** termos permitem o modelo multi-cliente | **Arquitetura B**: backend próprio + Tuya Cloud (Flagship ou plano negociado) |
| Só a Flagship de **US$ 25 mil/ano**, sem plano de piloto | Manter a Tuya Cloud **só no POC** (sua casa, depuração) e escolher entre **D (app próprio sobre o App SDK, ~US$ 5 mil/ano)** e **C (Edge local: Zigbee aberto)** antes de qualquer piloto pago |
| Contrato **não** permite uso em benefício de terceiros | **C** ou **D**; B fica descartada |
