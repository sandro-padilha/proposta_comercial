# 07 · Plug-and-play e instalação

Selos: ✅ confirmado · 🟡 provável · 🔬 necessita teste.

## 1. "Plug-and-play" em quatro níveis (não prometa o 4º no MVP)

| Nível | O que significa | Quem faz o quê | Alvo de tempo | Quando |
|---|---|---|---|---|
| **0. Manual** | Cadastro por código/SQL | Você | dias | POC |
| **1. Assistido** | **Console do instalador**: criar casa → template → conectar conta → importar → *auto-match* → "piscar para identificar" → testar → publicar | Técnico, sem programar | **≤ 4 h** num 45 m² | **MVP 1–2** |
| **2. Pré-provisionado** | Kit **Zigbee** pareado e nomeado na oficina; no cliente só se liga o gateway e se confirma | Técnico (e/ou cliente) | 1–2 h | MVP 3 (depende de 🔬 transferência de casa) |
| **3. Autoatendimento** | QR no kit → app/PWA da marca → pareamento guiado (App SDK da Tuya, Rota B) | Cliente | minutos | Produto 1.0+ e só se a Rota B se confirmar |

## 2. Reduzir o fluxo de 8 passos

Seu fluxo (`instalar → cadastrar → identificar → ambiente → objeto → vincular → testar → entregar`) vira:

| # | Passo original | O que automatizar | Ganho |
|---|---|---|---|
| 1 | Instalar dispositivos | **Padrão de nomes** no Smart Life: `Ambiente · Função` (ex.: `Sala · Luz principal`); kit etiquetado por slot | Elimina a maior parte da ambiguidade |
| 2 | Cadastrar dispositivos | **Importação** da conta vinculada (lista + `specification`) | Zero digitação |
| 3 | Identificar | Normalização DP → capacidade; categoria define o que o dispositivo *pode* ser | Zero decisão técnica |
| 4–6 | Escolher ambiente, objeto 3D, vincular | **Auto-match** (seção 3); só as ambiguidades viram pergunta | De N decisões para ~2–4 |
| — | (novo) Distinguir dois dispositivos iguais | **"Piscar para identificar"** (seção 4) | Resolve o caso das 6 lâmpadas iguais |
| 7 | Testar | **Checklist ao vivo** por slot (comando → retorno do estado) | Prova objetiva, vira relatório |
| 8 | Entregar | **QR de convite** + PWA + cartão de voz + relatório PDF | Entrega padronizada |

## 3. Auto-match: como o sistema associa sozinho

Entrada: dispositivos importados (nome, `category`, capacidades) × slots do template (`kind`, `accepts`, `room`).

```text
para cada dispositivo importado d:
  candidatos = slots livres onde kind/accepts são compatíveis com as capacidades de d   (filtro duro)
  pontuação(slot) =
      +50  nome de d contém o ambiente do slot (normalizado: "Sala", "Quarto 1", "Cozinha")
      +30  nome de d contém a função ("luz principal", "ar", "tv", "porta")
      +10  ordem de pareamento coincide com a ordem do slot (kits etiquetados)
      -∞   slot já usado
  se melhor − segundo melhor ≥ 25  → vincula automaticamente
  senão → vai para "Revisar" com os 2–3 melhores candidatos
```

- **Convenção de nome** = melhor investimento. Se o instalador seguir `Sala · Luz principal`, o auto-match acerta quase tudo.
- Slots `required: true` do template que ficarem sem vínculo **bloqueiam a publicação** (com opção de "marcar como não instalado" e esconder o objeto).
- Dispositivos sem slot compatível aparecem como "sobrando" (podem virar objetos genéricos no 3D).

## 4. "Piscar para identificar"

Quando há ambiguidade (6 lâmpadas iguais, 2 tomadas): o console emite um comando que **pisca** o dispositivo (liga/desliga 3×) enquanto o instalador olha o cômodo e toca em **qual objeto 3D** acendeu. Para **sensores** (sem atuador): *"acione o sensor agora"* — o console escuta o fluxo de eventos e associa o primeiro evento recebido. Ambos usam o mesmo caminho de comando/evento do produto, então **também testam a integração**.

## 5. Console do instalador (telas do wizard)

1. **Nova casa** — dados do cliente, endereço (grosso), template (45 m², 1 quarto…), data.
2. **Conectar conta** — instruções + QR; Rota A: vínculo no console da Tuya (**manual por conta**, gargalo conhecido); Rota B: o cliente já está no app da marca.
3. **Importar** — lista de dispositivos com categoria, *online*, bateria.
4. **Auto-match** — tabela slot ↔ dispositivo com confiança; "Revisar" abre o 3D com o slot piscando.
5. **Identificar** — botão "piscar" por dispositivo.
6. **Testar** — cada slot: comando de ida e volta com cronômetro; sensores: "acione agora"; IR: "o ar ligou?" (confirmação humana, pois IR é mão única).
7. **Cenas e alertas** — cenas do template (*Cheguei, Boa noite, Cinema*) com ações já ligadas aos slots; ativar 2–3 alertas padrão.
8. **Publicar e entregar** — QR de convite do cliente, instalação do PWA, cartão de comandos de voz, **relatório de entrega (PDF)** com mapa, lista de dispositivos, fotos e testes.

## 6. Templates de residência

```text
Template: APARTAMENTO 45 m² (1 quarto)
  Sala      ── luz principal (power, brightness) · TV (IR) · ar (IR/hvac) · sensor de temperatura
  Quarto    ── luz · ar (IR/hvac)
  Cozinha   ── luz
  Entrada   ── fechadura (lock, battery) · sensor de porta (contact) · sensor de movimento
  Energia   ── tomada medidora da geladeira / do ar
Cenas: Cheguei · Saí · Boa noite · Cinema
Alertas: porta aberta com modo "ausente" · consumo acima de X · bateria baixa
```

Fluxo para um novo cliente: **escolher template → ajustar parâmetros (cores, móveis opcionais, espelhamento) → importar dispositivos → vincular → publicar**. Estrutura técnica e manifesto em [05](05-painel-3d-e-valor-percebido.md) §3.

## 7. QR codes: três usos diferentes

| QR | Para quê | Observação |
|---|---|---|
| **Convite** | Cliente entra na casa (login por e-mail/OTP) e instala o PWA | Token guardado só como hash; expira |
| **Etiqueta de slot** | Colada no dispositivo/caixa do kit: `SALA-LUZ-1`; reforça o auto-match na instalação | Custa centavos |
| **Vínculo Tuya** | Rota A: escaneado no app Smart Life para ligar a conta ao projeto | Manual, feito pelo console da Tuya; some na Rota B |

## 8. Kits pré-provisionados: a estratégia **Zigbee-first**

- Dispositivos **Wi-Fi** guardam a rede em que foram pareados: se o cliente tem outro SSID/senha, é preciso **repareá-los** no local.
- Dispositivos **Zigbee** pareiam ao **gateway**, não ao Wi-Fi: o kit pode ser **pareado e nomeado na oficina**; no cliente só o **gateway** (um dispositivo Wi-Fi) é configurado.
- Por isso, para sensores, botões e tomadas, **prefira Zigbee**: também dura mais na bateria. Lâmpadas e hub IR costumam ser Wi-Fi.
- Falta validar 🔬: **transferir** a "casa" do Smart Life da conta de oficina para a do cliente. Alternativa mais simples: **o instalador cria a conta do cliente no local** (5 min) e pareia tudo nela.
- Regra de ouro de Wi-Fi: **2,4 GHz**; reserva de DHCP para o hub IR/gateway; roteador do cliente com sinal no ponto de cada dispositivo (teste com o celular antes).

## 9. Orçamento de tempo (apartamento 45 m², Essencial/Conforto)

| Etapa | Tempo |
|---|---|
| Pré-staging na oficina (etiquetas, firmware, pareamento Zigbee) | 1 h (fora do cliente) |
| Verificar Wi-Fi 2,4 GHz e pontos de instalação | 15 min |
| Instalar lâmpadas, sensores, tomadas, hub IR | 60–90 min |
| Parear no Smart Life e nomear no padrão | 30–45 min |
| Vincular conta, importar, auto-match, identificar | 20–30 min |
| Aprender IR / escolher marca do split | 20–30 min |
| Cenas e alertas do template | 10 min |
| Alexa: ativar skill, descobrir, testar voz | 15 min |
| Teste final, treinamento do cliente, entrega | 20–30 min |
| **Total no cliente** | **≈ 3,5 a 4,5 h** |

(Estimativa a validar no piloto — hipótese H4 em [05](05-painel-3d-e-valor-percebido.md).)

## 10. Reduzir suporte

| Medida | Efeito |
|---|---|
| **Catálogo homologado** (`/devices`): poucos SKUs testados, com DPs, escalas, notas e fornecedor | Menos surpresas de firmware/DP; compra com NF e garantia |
| **Painel de saúde por casa**: dispositivos *offline* > 24 h, bateria < 20 %, idade do último evento, erros de API | Suporte proativo em vez de reativo |
| **Diagnóstico remoto**: ver a casa do cliente (papel `support`, só leitura + comandos não críticos) | Resolve a maioria sem visita |
| **Guia curto do roteador** (2,4 GHz, DHCP, repetidor) e cartão de baterias | Previne os chamados mais comuns |
| **Alertas ao instalador** (não ao cliente) para falhas técnicas | Cliente não vira o monitor do sistema |
| **Atualização do painel** por PWA (sem visita) | Correções chegam sozinhas |

## 11. Conformidade e segurança física

| Tema | Orientação | Selo |
|---|---|---|
| **Anatel** | Dispositivos Wi-Fi/Bluetooth/Zigbee vendidos no Brasil exigem homologação; compre de **fornecedores nacionais com NF e selo**; evite importação sem selo (risco legal e de garantia) | 🟡 |
| **INMETRO** | Plugues/tomadas/interruptores têm regras próprias; confirmar antes de revender tomadas inteligentes | 🔬 |
| **Instalação elétrica** | Qualquer obra no quadro ou nas caixas de parede (relés, medidor de circuito) exige **profissional habilitado** e a NBR 5410. Em imóveis alugados, **prefira lâmpadas, tomadas medidoras, botões sem fio e sensores adesivos** | ✅ prática; norma a confirmar |
| **Fechadura** | Troca de cilindro exige anuência do proprietário; nunca "fail-open"; chave física sempre | ✅ prática |
| **LGPD** | Contrato/termo de uso, política de privacidade, consentimento para dados de presença, retenção de 90 dias, exportação e exclusão | 🟡 validar com advogado |
| **Garantia** | Prazo e quem responde (integrador × fabricante); processo de troca | A definir |
