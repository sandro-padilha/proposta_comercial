# 05 · Painel 3D e valor percebido

Selos: ✅ confirmado · 🟡 provável · 🔬 necessita teste ([01](01-evidencias-e-pesquisa.md)).

## 1. Tecnologia: o que usar

| Opção | Desempenho | Dev. / manutenção | Celular · tablet · TV | Veredito |
|---|---|---|---|---|
| **Three.js puro** (como a referência) | Máximo controle | Muito boilerplate; estado e UI à mão | Bom | Boa base, mas caro de manter em equipe pequena |
| **React Three Fiber + drei** (sobre Three.js) | Igual ao Three | **Declarativo**: cada objeto inteligente vira um componente; `frameloop="demand"` e `invalidate()` ✅ (R3F 9.8.1) | Bom | **Recomendado** |
| **Babylon.js 9** | Muito bom | Engine completa, Inspector ótimo; bundle maior; integração com React menos natural | Bom | Alternativa válida se a equipe preferir "tudo em um" |
| `<model-viewer>` (Google) | Leve | Trivial, mas sem hotspots/estado customizados | Bom | Não serve para interface de controle |
| SVG/CSS isométrico 2.5D | Muito leve | Simples | **Roda em qualquer TV/navegador** | **Usar como fallback** ("modo lista/2.5D") |
| Unity/Unreal WebGL | Pesado | Overkill | Ruim | ⛔ |

Versões atuais (2026-10-01, npm ✅): `three` 0.186.1 · `@react-three/fiber` 9.8.1 · `@react-three/drei` 10.7.9 · `babylonjs` 9.29.0. Licenças MIT (Three/R3F/drei) e Apache-2.0 (Babylon). **WebGL2 basta**; WebGPU é irrelevante para o MVP (W3).

### Onde roda

| Alvo | Como | Selo |
|---|---|---|
| Celular (Android/iOS) | **PWA** instalável; WebGL2; cache offline do GLB e do shell | ✅ técnica · iOS Web Push exige PWA instalada 🟡 |
| Tablet de parede | PWA/navegador em modo quiosque; modo "tela sempre ligada" com render sob demanda (bateria) | 🔬 |
| Navegador desktop | Direto | ✅ |
| **Smart TV** | TVs Samsung usam Chromium M94 (2023) / M108 (2024) 🟡; webOS 🔬. O desempenho 3D em TV é incerto → **modo lista/2.5D como padrão na TV** | 🔬 S6 |
| Alexa Echo Show | Navegador Silk: abrir a URL do painel | 🔬 |
| App de loja (iOS/Android) | **Capacitor 8** envolvendo a mesma PWA, quando houver necessidade (push nativo, loja) | ✅ pacote existe |

### Orçamento de desempenho (proposta; a referência prova que cabe)

A referência roda ~**250 draw calls e ~252 mil triângulos** num prédio gigante, com 26 luzes reais ([02](02-referencia-igreja-3d.md)). Para um apartamento, o orçamento pode ser bem menor:

| Métrica | Meta | Observação |
|---|---|---|
| Tamanho do GLB | **≤ 3 MB** | Meshopt + texturas WebP/KTX2 (`gltf-transform optimize`) |
| Draw calls | ≤ 150 | Fusão de malhas por material; instâncias |
| Triângulos | ≤ 150 mil | Estilo *low-poly* |
| Luzes reais | **0–4** | Luz "falsa": emissivo + halo + "poça de luz" no piso; sombra assada (AO) |
| Resolução | DPR ≤ 2; governador por tempo de quadro | Reduz em movimento, nítido ao parar |
| Redesenho | **Sob demanda** (`frameloop="demand"`) | Parado = 0 quadros; bateria e esquentamento |
| Carga inicial | < 3 s em 4G; GLB em cache depois | PWA |

## 2. Estilo visual: *dollhouse* estilizado, não fotorrealismo

Corte de casa de boneca (paredes baixas, sem teto), cores limpas, luz assada. É **mais barato de produzir**, **esconde imprecisões** de medida, roda em aparelhos simples e, bem executado, parece premium. Fotorrealismo por cliente é o caminho para a ruína de margem ([02](02-referencia-igreja-3d.md) §4).

## 3. Como um objeto 3D vira objeto inteligente

Três camadas, cada uma com um dono:

```text
GLB (template)         →  nó "obj.sala.luz_principal"  + extras { casa3d: { slot, kind } }      [artista]
Manifesto (template)   →  slot "sala.luz_principal": aceita [power, brightness], comportamento   [template]
Vínculo (por casa)     →  slot ↔ capacidades de dispositivos reais                               [instalador]
```

**Verificado ✅ no código do Three.js:** o `GLTFLoader` copia `extras` de cada nó do glTF para `object.userData` (função `assignExtrasToUserData`, aplicada a nós, malhas, cenas etc.). No Blender, as *Custom Properties* exportam como `extras` 🟡 (conferir a opção do exportador glTF no S6). Portanto o motor 3D encontra os objetos por `userData.casa3d.slot`, sem convenção frágil de nomes.

### 3.1 Manifesto do template (exemplo)

```json
{
  "schema": "casa3d.template/1",
  "template": "apto-45m2-1q",
  "version": 3,
  "model": { "glb": "templates/apto-45m2-1q/v3/model.glb", "sha256": "…", "units": "m", "up": "Y" },
  "cameras": [
    { "id": "overview", "pos": [8, 9, 10], "target": [0, 0.8, 0] },
    { "id": "sala",     "pos": [2, 3.5, 4], "target": [0, 0.8, 0] }
  ],
  "rooms": [
    { "slug": "sala",   "name": "Sala",   "camera": "sala" },
    { "slug": "quarto", "name": "Quarto", "camera": "quarto" }
  ],
  "slots": [
    { "key": "sala.luz_principal", "kind": "light",  "room": "sala",    "accepts": ["power", "brightness"], "required": true,
      "behavior": { "type": "light", "glow": "#ffd9a0", "pool": true } },
    { "key": "sala.tv",            "kind": "tv",     "room": "sala",    "accepts": ["power"], "behavior": { "type": "tv", "presumed": true } },
    { "key": "sala.ar",            "kind": "ac",     "room": "sala",    "accepts": ["hvac"],  "behavior": { "type": "ac", "presumed": true } },
    { "key": "entrada.porta",      "kind": "door",   "room": "entrada", "accepts": ["contact"] },
    { "key": "entrada.fechadura",  "kind": "lock",   "room": "entrada", "accepts": ["lock", "battery"], "critical": true }
  ],
  "scenes": [
    { "key": "boa_noite", "name": "Boa noite", "icon": "moon",
      "steps": [ { "slot": "sala.luz_principal", "cmd": "off" }, { "slot": "sala.tv", "cmd": "off" }, { "slot": "entrada.fechadura", "cmd": "lock" } ] }
  ]
}
```

### 3.2 Vínculo (por casa): seus dois exemplos

Luz da sala (antes `light_sala_01`):

```jsonc
{
  "object": "sala.luz_principal",
  "bindings": [
    { "role": "primary", "device": "tuya:bf0123…", "code": "switch_led",      "kind": "power" },
    { "role": "aux",     "device": "tuya:bf0123…", "code": "bright_value_v2", "kind": "brightness" }
  ]
}
```

Porta principal (antes `door_main`):

```jsonc
{
  "object": "entrada.fechadura",
  "bindings": [
    { "role": "primary", "device": "tuya:bf9876…", "code": "lock_motor_state",   "kind": "lock" },
    { "role": "battery", "device": "tuya:bf9876…", "code": "battery_percentage", "kind": "battery" }
  ]
}
```

No banco isso é `objects` + `object_bindings` + `capabilities` ([06](06-modelo-de-dados.md)): `slot_key` humano e estável, **ids opacos** por baixo.

### 3.3 Comportamentos (catálogo reutilizável)

Cada `kind` tem um componente R3F que mapeia **estado → visual**. Nenhum código por cliente.

| `kind` | Estado → visual | Toque |
|---|---|---|
| `light` | Emissivo + halo + "poça de luz"; dimmer controla intensidade; cor se RGB | Alterna; segurar abre intensidade/cor |
| `plug` / `energy` | Selo de watts (kWh no detalhe) | Alterna (plug) |
| `ac` | LED por modo (frio/quente/seco), **selo "presumido"** (IR é mão única) | Folha: liga/desliga, °C, modo, ventilador |
| `tv` | Tela acesa/apagada (inferida por consumo, se houver tomada medidora) | Liga/desliga |
| `door` / `window` / `contact` | Folha abre ou ícone; cor de alerta | Mostra histórico |
| `lock` | Cadeado verde/vermelho, bateria; **PIN para abrir** | Folha com confirmação |
| `motion` / `presence` | Pulso suave ao detectar | Histórico |
| `climate_sensor` | Rótulo °C / % | — |
| `scene_button` | Botão no HUD | Executa cena |

## 4. UX: "entrar, ver a casa, tocar, controlar"

- **Barra de estado de relance:** `3 luzes acesas · porta trancada · 1,42 kW · ar do quarto ligado`. Aqui está **metade do valor**: responder "está tudo certo em casa?" em 1 segundo.
- **Câmera por ambiente** (botões `Sala / Quarto / Cozinha`) em vez de navegação livre desde o dia 1.
- **Cenas na base** (*Cheguei*, *Boa noite*, *Cinema*) e **folha de detalhes** (bottom sheet) para dimmer, ar e fechadura.
- **Modo lista/cartões sempre disponível** (acessibilidade, TV, aparelhos fracos, perda do WebGL).
- Estados explícitos: *carregando*, *sem conexão — último estado às 21:42*, *dispositivo offline*, *comando sem resposta*.
- Alvos de toque ≥ 44 px, `prefers-reduced-motion`, legendas legíveis, contraste.
- Atualização otimista com reversão em ~5 s.

## 5. Personalização sem retrabalho: templates e geração

| Nível | O que é | Esforço por cliente | Quando |
|---|---|---|---|
| **1. Catálogo de templates** | 3–6 plantas típicas modeladas uma vez no Blender (studio 30 m², 1 quarto 45 m², 2 quartos 55–70 m², casa pequena); variações por **parâmetros** (cor de parede/piso, móveis opcionais, espelhamento) | **1–2 h** | MVP 1–2 |
| **2. Gerador paramétrico** | Planta 2D em JSON (cômodos, paredes, portas, janelas) → paredes/pisos extrudados em runtime + biblioteca de móveis e objetos GLB instanciados; editor 2D com *snap* | 1–3 h | MVP 3 |
| **3. Sob medida (premium)** | Modelagem manual para quem paga a mais | 6–16 h | Serviço extra |

Entradas alternativas para a planta: arquivo do **Sweet Home 3D** (exporta OBJ, comum com arquitetos/decoradores) 🟡; foto/PDF da planta convertido por IA — **prova de que é viável: a Samsung faz exatamente isso no SmartThings** ✅ (C1), porém é trabalho próprio; **LiDAR do iPhone** (RoomPlan) 🔬. Custo de modelagem de um template: 2–4 dias de artista (R$ 1,5–4 mil) — **hipótese** a cotar.

## 6. Valor percebido: o 3D realmente vende?

**Resposta honesta: é plausível, mas não está provado.** E o 3D **sozinho já não é um diferencial raro**: a Samsung oferece **SmartThings Map View 3D** incluído no app SmartThings (sem cobrança separada informada), gerado por foto da planta, endereço, desenho ou LiDAR de aspirador, em celular e **em TVs Samsung** ✅ (C1). Isso valida o *conceito* e, ao mesmo tempo, avisa que "tem 3D" não basta.

### Produto genérico × produto proposto

| Dimensão | App genérico Tuya/Smart Life | Casa 3D |
|---|---|---|
| Orientação espacial | Lista de dispositivos por nome | **Planta viva do próprio apartamento** |
| "Está tudo certo em casa?" | Abrir vários cartões | **Uma olhada** |
| Onboarding da família | Aprender nomes de dispositivos | "Toque no que você vê" |
| Cenas e alertas | Sim, com configuração | Sim, **já entregues pelo instalador** |
| Experiência de venda | Sem impacto | **Demonstração em 30 s** |
| Marca e suporte | Fabricante genérico | **Integrador local, pt-BR, com instalação** |
| Exclusividade percebida | Nenhuma | Alta, se o modelo for **do apê do cliente** |

### O que aumenta valor × o que é só efeito

| Elemento | Classificação | Por quê |
|---|---|---|
| Estado real refletido no 3D | **Aumenta valor** | É a função: ver o que está ligado |
| Barra de estado e alertas (porta, consumo) | **Aumenta valor** | Reduz preocupação; justifica assinatura |
| Cenas entregues prontas | **Aumenta valor** | Entrega "casa inteligente" no dia 1 |
| Modelo **da casa do cliente** (planta/cores) | **Justifica preço maior** | Personalização é percebida como "feito para mim" |
| Voz (Alexa) | Aumenta valor (parceiro) | Já é expectativa do mercado |
| Câmera por ambiente, transições suaves | Valor médio, custo baixo | Dá acabamento |
| Dia/noite e clima | Efeito agradável | Imersão barata |
| Caminhar em 1ª pessoa, animação de fluxo de ar, maçanetas | **Só efeito visual** | *Wow* de demo; quase nunca usado no dia a dia |
| Fotorrealismo, reflexos, sombras dinâmicas | **Custo sem retorno** | Pesa em celular/TV e encarece cada template |
| Modelagem manual por cliente | **Custo sem retorno** | Destrói a margem |

### Hipóteses a testar (antes de construir o produto)

| ID | Hipótese | Experimento | Critério de sucesso (proposta) |
|---|---|---|---|
| H1 | Quem vê o 3D do **próprio** apê paga mais | Mostrar protótipo do apê de 10 prospects ao lado do app Tuya | ≥ 3 de 10 aceitam pagar ≥ R$ 500 a mais |
| H2 | O painel é usado depois da demo | Instrumentar pilotos (aberturas/dia, toques/dia) | ≥ 3 aberturas/dia por casa na 3ª semana |
| H3 | A barra de estado reduz o "esqueci ligado" | Pergunta pós-piloto + eventos | NPS ≥ 8 e relato espontâneo de uso |
| H4 | Instalação em ≤ 4 h com template | Cronometrar | Mediana ≤ 4 h |

## 7. Roadmap do 3D por valor

| Fase | Entra | Fica de fora |
|---|---|---|
| **POC** | 1 cômodo + 3 objetos (luz, TV/AC por IR, sensor), estado ao vivo, modo lista | Templates, edição, cenas |
| **MVP 1** | 1 template (45 m²), 8–12 slots, câmeras por ambiente, barra de estado, cenas, PWA, qualidade adaptativa simples | Dia/noite, vista de cima, caminhada |
| **MVP 2** | 3 templates, fechadura e energia no 3D, vista de cima, dia/noite, alertas visuais | Gerador paramétrico |
| **MVP 3** | Editor/gerador de planta, marca branca por parceiro | Modo "Pessoa", fotorrealismo |
