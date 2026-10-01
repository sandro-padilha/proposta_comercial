# 01 · Evidências e pesquisa

Data da pesquisa: **2026-10-01**. Este documento separa o que foi **verificado** do que é **provável** ou **precisa de teste**, como pedido no briefing.

| Selo | Significado |
|---|---|
| ✅ **Confirmado** | Verificado em fonte primária: código-fonte oficial/aberto que baixei e li, teste que executei, ou várias fontes concordantes. |
| 🟡 **Provável** | Veio de resumo de busca, fonte secundária ou conhecimento prévio; é coerente, mas **não li a página oficial**. Trate como hipótese forte, não como fato. |
| 🔬 **Necessita teste** | Só se resolve com dispositivo, conta ou console reais. Está no plano de spikes (seção 4). |
| ⛔ **Não recomendado** | Possível ou até funcional, mas inadequado para um produto comercial. |

## 1. Limites deste estudo (leia primeiro)

O ambiente em que fiz a pesquisa **bloqueia por política de rede** os hosts abaixo, então **não consegui ler** as páginas oficiais mais importantes para a decisão comercial:

`developer.tuya.com` · `support.tuya.com` · `tuya.com` · `www.tuya.com` · `developer.amazon.com` · `supabase.com` · `www.home-assistant.io` · `community.home-assistant.io` · `apis.io` · `lgrsv.github.io`

Consequências:

- **Preços e termos comerciais da Tuya** (o ponto mais crítico) estão como 🟡. Nenhuma decisão de investimento deve se apoiar neles sem confirmação direta (seção 5).
- **A demo da referência** (`lgrsv.github.io/igreja-3d-v1`) não pôde ser aberta; analisei o **repositório público** que a publica, via clone raso (commit `369a5fd`, 2026-09-30). Ver [02](02-referencia-igreja-3d.md).
- Para destravar: *menu do ambiente na barra de título da sessão → Edit → Network access* → liberar os hosts acima (ou um nível de acesso mais amplo). Com isso eu reabro e atualizo este documento.

O que **pude** usar: busca na web (resumos), `github.com`, registros **npm** e **PyPI** (baixei e li os SDKs oficiais da Tuya), Postgres 16 local e Node 22 locais para executar testes.

## 2. Tabela de evidências

### Tuya

| # | Afirmação | Selo | Base |
|---|---|---|---|
| T1 | Trial do IoT Core: **50 dispositivos conectados e 10 controláveis** | 🟡 | Dois resultados de busca concordantes (a lista de fontes incluía páginas de suporte da Tuya, que não consegui abrir) |
| T2 | Trial: **26 mil chamadas de API e 68 mil mensagens por mês** | 🟡 | Um resultado de busca; os números de cota precisam ser reconfirmados |
| T3 | O trial pode ser **renovado de graça** (até 6 meses por vez) | ✅/🟡 | A wiki oficial `tuya/tuya-home-assistant` (lida) diz que após expirar se estende de novo em *Cloud → My Services*; o prazo de 6 meses vem de resumo de busca |
| T4 | Estourou a cota: o serviço é **restringido até virar o mês** | 🟡 | Resumo de busca + aviso citado na issue `tuya-home-assistant#804` ("Once the quota limit is exceeded, the service will be suspended") |
| T5 | Edições comerciais **Flagship/Corporate** têm cotas enormes (≈224 M / 426 M chamadas por mês; até 75 mil / 200 mil dispositivos) | 🟡 | Resumo de busca |
| T6 | Preço dessas edições: **US$ 25 mil e US$ 50 mil por ano** (moeda e periodicidade presumidas pelo contexto) | 🟡 (2022) | Issue #804 (maio/2022, lida): *"25K ou 50K for Corporate or Flagship edition"*; resumos de busca repetem. **Preço atual não confirmado** |
| T7 | Recursos extras (Flagship, fora da China): ≈ **US$ 3,15 por milhão de chamadas** e **US$ 1,24 por milhão de mensagens** | 🟡 | Resumo de busca |
| T8 | "Self-Developed App Official" (app com marca própria): **US$ 5 mil no 1º ano e US$ 2 mil na renovação**, domínio próprio, até 100 M chamadas/mês | 🟡 | Resumo de busca de página comercial da Tuya; **escopo exato desconhecido** |
| T9 | O fluxo "QR code + User Code" do Home Assistant é **específico do HA**: `client_id = HA_3y9q4ak7g4ephrvke`, `schema = haauthorize`, rotas `/v1.0/m/life/home-assistant/qrcode/...` e `/v1.0/m/life/ha/...` | ✅ | Código do HA e do `tuya-device-sharing-sdk` 0.2.15 (MIT) lidos |
| T10 | Usar o *Device Sharing* como base de produto comercial | ⛔ | Consequência de T9: seria usar credenciais registradas para outro produto |
| T11 | Assinatura da Open API: `HMAC-SHA256(secret, client_id + access_token + t + stringToSign)`, token em `GET /v1.0/token?grant_type=1`, refresh em `/v1.0/token/{refresh}` | ✅ | SDK Python e SDK Node oficiais lidos; **5 vetores idênticos** no meu TypeScript (`poc/tuya-core`) |
| T12 | Eventos em tempo real: **Pulsar sobre WebSocket**; URL `…/ws/v2/consumer/persistent/{id}/out/event/{id}-sub…`, senha `md5(id+md5(secret))[8:24]`, payload AES-128-ECB com chave `secret[8:24]` | ✅ | SDK `tuya-connector-python` 0.1.2 lido; senha, URL e decriptação reproduzidas em TS e validadas contra o SDK |
| T13 | O SDK Python da Tuya **desativa a verificação TLS** (`ssl.CERT_NONE`) | ✅ | Lido em `openpulsar.py`. Não copiar |
| T14 | Mensagens com `encryptModel` GCM | 🔬 | Meu código recusa explicitamente; implementar só após ver uma mensagem real |
| T15 | Rotas de leitura: `/v1.0/iot-03/devices/{id}/status`, `/specification`, `/functions`, lista `/v1.0/iot-03/devices` | ✅ | SDK Node oficial `@tuya/tuya-connector-nodejs` 2.1.2 |
| T16 | Rota de **envio de comandos** `POST /v1.0/iot-03/devices/{id}/commands` | 🟡/🔬 | O caminho `/commands` existe no SDK Node (apenas como GET); o POST é o padrão documentado, mas não o vi em código — testar no primeiro dia |
| T17 | **IR**: `…/infrareds/{ir}/air-conditioners/{remote}/command` e `/scenes/command` (power, mode, temp, wind), `/remotes/{id}/keys`, `/remotes/{id}/raw/command` | ✅ | Código da integração open-source `EnzoD86/tuya-smart-ir-ac` (lido) |
| T18 | **Fechadura**: abertura remota via `/door-lock/password-ticket` + `/door-lock/password-free/open-door` | 🟡 | Resumo de busca de documentação *miniapp* da Tuya; modelos compatíveis e serviço adicional: 🔬 |
| T19 | Uma conta de app (Smart Life) só pode estar ligada a **2 projetos** de nuvem | 🟡 | Comunidade (Homey) |
| T20 | O data center do projeto **precisa casar** com o da conta do app; Tuya "proibirá chamadas entre regiões" | ✅ | Wiki oficial `tuya-home-assistant` (lida) |
| T21 | Contas do Brasil caem no data center "Américas" (`openapi.tuyaus.com`) | 🔬 | Os SDKs só listam `us/eu/in/cn/sg`; confirmar no 1º vínculo |
| T22 | Controle **local** (LAN): protocolos 3.1–3.5, **uma conexão TCP por dispositivo**, dispositivos a bateria não funcionam localmente, exige `local_key` obtida via conta de nuvem | ✅ | README do `tinytuya` (MIT) lido |

### Alexa / Amazon

| # | Afirmação | Selo | Base |
|---|---|---|---|
| A1 | Smart Home Skill API suporta **pt-BR** (endpoint América do Norte; Lambda em us-east-1) | 🟡 | Resumo da página oficial *Develop Smart Home Skills for Multiple Languages* |
| A2 | Skill em desenvolvimento pode ter **beta com até 500 usuários por até 90 dias** | 🟡 | Doc de custom skills; vale para smart home: 🔬 |
| A3 | Skills de casa inteligente exigem **account linking OAuth 2.0**, testes de certificação e credenciais de teste por idioma | 🟡 | Resumo da doc oficial. **Prazo de certificação não confirmado** |
| A4 | A skill **Smart Life** da Tuya funciona no Brasil ("Works with Alexa") | 🟡 | Resultado de busca; teste de 10 min no app Alexa |
| A5 | Alexa **não** oferece API oficial para receber eventos de dispositivos de *outras* skills | 🟡 | Conhecimento prévio; coerente com a arquitetura de skills |

### Concorrência e mercado

| # | Afirmação | Selo | Base |
|---|---|---|---|
| C1 | **SmartThings Map View 3D**: planta por foto, endereço, desenho ou LiDAR de aspirador Samsung vira layout 3D com dispositivos; em Android, iOS e **TVs Samsung** | ✅ | Samsung Newsroom (vários resultados) |
| C2 | Anatel: dispositivos Wi-Fi/Bluetooth comercializados no Brasil exigem **homologação** (Res. 242/2000) | 🟡 | Resumos de busca; validar com especialista |
| C3 | INMETRO para plugues/tomadas inteligentes | 🔬 | Não confirmado nos resultados |
| C4 | Preços de varejo BR (2026): lâmpada Wi-Fi **R$ 26–50**; hub IR **R$ 40–100**; sensor de porta/janela **R$ 80–112**; tomada com medidor **R$ 35–130**; Echo Dot 5ª ger. **R$ 354–429**; fechadura Wi-Fi (app Tuya) **R$ 318–1.780** | 🟡 | Anúncios em varejistas/comparadores |

### Stack web (registros npm, 2026-10-01)

| # | Afirmação | Selo | Base |
|---|---|---|---|
| W1 | Versões atuais: `three` **0.186.1** · `@react-three/fiber` **9.8.1** · `@react-three/drei` **10.7.9** · `babylonjs` **9.29.0** · `vite` **8.3.2** · `react` **19.3.0** · `@supabase/supabase-js` **2.117.2** · `fastify` **5.12.5** · `@capacitor/core` **8.5.2** · `workbox-build` **7.4.1** · `@gltf-transform/cli` **4.5.1** · `ws` **8.22.0** | ✅ | `npm view` |
| W2 | Licenças: **MIT** (three, R3F, drei, supabase-js, ws, tuyapi, tuya-connector-nodejs, `zigbee-herdsman` e `-converters`); **Apache-2.0** (Babylon, matter.js, pulsar-client) | ✅ | `npm view … license` |
| W3 | WebGPU em todos os navegadores principais | 🟡 | Resumo de blog; **irrelevante para o MVP** (WebGL2 basta) |
| W4 | TVs Samsung usam Chromium M94 (2023) / M108 (2024); webOS e desempenho 3D | 🟡 / 🔬 | Doc Samsung (resumo); testar em TV real |
| W5 | Supabase Pro: **US$ 25/mês**, 100 mil MAU, 8 GB de banco, 250 GB de banda, 500 conexões Realtime simultâneas | 🟡 | Guias secundários de 2026 |

## 3. Verificações que eu mesmo executei

| O quê | Resultado |
|---|---|
| Assinatura Tuya (TS) vs. SDK Python oficial, 5 casos (token, status, query desordenada, POST com corpo, IR) | ✅ idênticas |
| Senha, URL e decriptação do Pulsar (TS) vs. SDK Python oficial | ✅ idênticas |
| Consumidor Pulsar contra servidor WebSocket simulado: valida cabeçalhos, entrega evento, faz ACK, reconecta após queda | ✅ |
| Cliente Tuya com `fetch` falso: token reutilizado, refresh, corpo assinado = corpo enviado, erro tipado, retry de token inválido | ✅ **22 testes passam** (`poc/tuya-core`) |
| Schema multi-tenant em **PostgreSQL 16 real**: isolamento entre clientes/organizações, papéis, GRANTs, FKs compostas, comando crítico, idempotência, snapshot, partições | ✅ **50 asserções passam** (`database/tests/run.sh`) |

**O que isso NÃO prova:** nenhuma chamada real à nuvem da Tuya foi feita (não há credenciais). Os testes provam que o *meu código* produz exatamente o que o *SDK oficial* produz; não provam que a Tuya aceitará uma conta/projeto específico.

## 4. Spikes de validação (1 semana, antes de gastar com o MVP)

Cada item tem critério de saída objetivo.

| Spike | Como | Saída esperada |
|---|---|---|
| **S1 · Tuya Cloud ponta a ponta** | Criar conta e projeto no console, escolher data center, assinar IoT Core (trial) e Message Service, vincular uma conta Smart Life por QR, listar dispositivos, ler `specification`, ligar uma lâmpada, receber o evento por Pulsar (usar `poc/tuya-core`) | Lâmpada comandada pelo meu código e evento recebido em < 2 s. **Confirma T16, T21, T14** |
| **S2 · IR e ar-condicionado** | Hub IR Wi-Fi + TV + split: `scenes/command`, `keys`, `raw/command` | Ligar o ar a 24 °C e mudar de canal por API |
| **S3 · Sensores e energia** | Sensor de porta, de movimento, tomada com medidor: observar **frequência real de mensagens** e polaridade de `doorcontact_state` | Tabela real de DPs, escalas e mensagens/dia por dispositivo |
| **S4 · Fechadura (opcional)** | Modelo candidato: testar abertura remota por API e o log de eventos | Sim/não por modelo, com a lista de requisitos (gateway, serviço) |
| **S5 · Alexa nativa** | Ativar a skill Smart Life, verificar luzes, cenas e sensores como gatilho de rotina, voz em pt-BR | Roteiro de instalação validado + limites reais |
| **S6 · 3D em 3 dispositivos** | Carregar um GLB de teste com 10 objetos em celular Android médio, iPhone, tablet barato e Smart TV | FPS, memória, tempo de carga; decisão sobre modo "lista" como fallback |
| **S7 · Resposta da Tuya** | Enviar o e-mail abaixo | Proposta escrita de custo por casa |

## 5. E-mail para a Tuya (modelo)

> Assunto: Licenciamento comercial de acesso à nuvem — integrador de automação residencial no Brasil
>
> Somos integradores de automação residencial no Brasil. Vamos instalar, em apartamentos, dispositivos Tuya/Smart Life (iluminação, IR, sensores, tomadas com medidor e, futuramente, fechaduras) e oferecer ao cliente um painel web próprio (3D) que lê estado e envia comandos via Open API. Precisamos entender o caminho **comercial** correto:
>
> 1. Qual edição/serviço é exigido para uso **comercial multi-cliente** da Open API e do Message Service? Qual o preço atual (fixo + variável) e as cotas?
> 2. Existe plano **para startups/pilotos** (até ~50 residências) com custo proporcional?
> 3. O vínculo da conta Smart Life do cliente ao nosso projeto (*Link Tuya App Account*) é permitido nesse modelo? Há limite de contas e de dispositivos?
> 4. Como é o caminho de **app com marca própria** (App SDK / "Self-Developed App"): preço, o que inclui, e se ele dá acesso à Open API para os usuários desse app?
> 5. Quais fechaduras suportam **abertura remota via API** e há serviço adicional?
> 6. O data center correto para contas brasileiras e a localização dos dados (LGPD).
>
> Obrigado.

## 6. Critério de decisão para a Tuya (Portão 1)

| Resposta da Tuya | Decisão |
|---|---|
| Custo variável por casa **≤ ~R$ 10/mês** (ou taxa fixa que se dilua nisso) e termos permitem o modelo | Seguir **Arquitetura B** (backend próprio + Tuya Cloud) |
| Só edição de **US$ 25–50 mil/ano** e sem plano de piloto | Manter Tuya Cloud **apenas no POC** (1–2 casas, trial) e migrar para **integração local (Zigbee + LAN) com Edge Box** antes de vender em escala — ver [03](03-arquitetura-e-stack.md) e [08](08-mvp-custos-negocio-riscos.md) |
| App próprio por ≈ US$ 5 mil/ano com acesso à API | Avaliar **App SDK** (melhora o plug-and-play); exige app nativo/híbrido |
