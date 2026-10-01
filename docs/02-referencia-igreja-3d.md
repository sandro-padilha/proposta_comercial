# 02 · Análise da referência: "Igreja 3D"

> **Como foi analisada.** Li o **código-fonte** do repositório público `LGRSV/igreja-3d-v1` (clone raso, commit `369a5fd`, 2026-09-30), que é o que a demo `lgrsv.github.io/igreja-3d-v1` publica. As observações de comportamento vêm do README e do código.

## 1. O que é

Um **cartão Lovelace para Home Assistant** (instalável por HACS) que mostra um modelo 3D da "Base Church" (802 Sul, Palmas-TO) em Three.js e o liga às entidades do HA: cada ambiente acende conforme o interruptor real, clicar alterna a entidade, o telão mostra o que toca, os LEDs dos ares refletem o modo, a porta de vidro abre quando o sensor abre. Existe também uma **demo standalone** (`index.html`) com estados simulados. O motor é derivado de outro projeto do mesmo autor (`casa3d-card`, repositório `casa-chefe`).

| Item | Valor |
|---|---|
| Arquivo principal | `igreja3d-card.js`: **9.474 linhas / ~685 KB**, módulo ES com Three.js **0.170.0 via CDN** (jsDelivr) |
| Decoração por área | `rooms/*.js`: **7 arquivos, 4.427 linhas**, colados no card por `integrate_rooms.py` |
| Geometria | **100% procedural em código** (`ZONES`, `ITEMS`, `_buildWalls()`, `_buildFurniture()`, funções `room…(ctx)`), em metros. **Não há arquivo glTF/GLB** |
| Histórico | 16 versões documentadas (v1.1 → v1.5.5), muitas delas ajustes de portas, escadas e acabamentos "conforme fotos e vídeos do cliente" |
| Licença | **Nenhum arquivo LICENSE** no repositório |
| Testes | Scripts headless (`tools/*.mjs`, Playwright + Chromium/SwiftShader) para navegação, caminhada, governador de qualidade, portas, ar, clique-para-andar |

## 2. Acoplamento com o Home Assistant

O card depende do HA em poucos pontos, o que é uma **boa notícia**: dá para trocar o adaptador sem mexer na cena.

| Ponto | Onde | Equivalente no nosso produto |
|---|---|---|
| Recebe o objeto `hass` | `set hass()` / `_syncFromHass()` (~l. 6259) | `StateStore` alimentado pelo Realtime |
| Lê estado | `hass.states[...]` (~l. 7855–7880) | `capability_state` (snapshot + deltas) |
| Envia comando | `hass.callService(...)` (~l. 8749–8828) | `POST /v1/commands` → `issue_command()` |
| Vínculo objeto ↔ dispositivo | `entities:` em YAML (chaves de exemplo como `palco`, `hall`, `ac_templo`) | tabela `object_bindings` ([06](06-modelo-de-dados.md)) |
| Dia/noite | `sun.sun` do HA, ou lat/long | cálculo local por data/lat/long (ou API de clima sem chave) |

## 3. O que ela faz muito bem (e vale como ideia)

Estas são **técnicas**, não código para copiar:

1. **Orçamento de desenho agressivo.** ~5.200 malhas fundidas por material: **5.152 → 250 draw calls**; instâncias para portas; ~252 mil triângulos.
2. **Poucas luzes reais.** 26 `PointLight`, só 8 com sombra no modo alto; **9 no modo "leve"** (celular/tablet) e **5 no "mínimo"**. O resto é "luz falsa": material emissivo + halo + "poça de luz" no piso.
3. **Níveis de qualidade** (`alta · media · leve · min`), escolhidos automaticamente por GPU/RAM/núcleos, e um **governador pelo tempo real de quadro**: baixa a resolução enquanto a câmera se move e entrega **um** quadro nítido ao parar.
4. **Render sob demanda.** Parado, **0 redesenhos**; liga/desliga luz não recompila shaders (todas as luzes ficam ativas com intensidade zero).
5. **Acessibilidade e bateria:** respeita `prefers-reduced-motion`, pausa com a aba oculta ou o card fora da tela.
6. **UX que funciona para leigos:** *Vista de cima navegável* (bloco → cômodo → aparelho, com trilha clicável e "Voltar"), painel inferior com abas (ambientes, rotinas, automações, atividade), contador "N de M luzes acesas", feedback otimista no clique.
7. **Estado visível de relance:** LED do ar por modo, porta que abre, telão aceso.
8. **Testes automatizados da camada visual** rodando sem GPU.

## 3.1 A demo rodando (observação)

Renderizei a demo (v1.5.5) em Chromium **sem GPU** (SwiftShader), com o Three.js servido localmente. O próprio card detectou o renderizador por software e foi para o nível `min`, com o log *"malhas estáticas: 4871 → 238 draw calls · luzes reais: 7 (0 com sombra) · qualidade: min"* e o **governador de qualidade descendo degraus** sozinho: o comportamento descrito no README se confirma. Por isso a imagem em si ficou simplificada (sem sombras, resolução reduzida); em GPU real o README indica um nível visual bem maior. O que a execução mostrou sobre a **experiência**:

- **A tela é metade 3D, metade cartões.** O 3D ocupa a parte superior; **abaixo há um painel de vidro com abas** (*Ambientes · Automações · Atividade*), filtros por área e **cartões de dispositivo** com ícone, estado ("acesa · 100%", "ligado", "Frio · 22° · 24,5° atual"), **tempo desde a última mudança** ("há 6 min") e brilho colorido por tipo (roxo no palco, âmbar nas luzes, azul no ar, rosa na presença). Um contador resume: **"9 de 14 luzes acesas"**. Ou seja: **a lista é parte central da interface, não um plano B**; o 3D dá o contexto espacial.
- **Estado refletido de verdade:** ao "acender tudo", a câmera **voou até o ar-condicionado que ligou**, com o fluxo de ar aparecendo; na **Vista de cima**, a trilha *‹ Voltar · Planta › Templo* e os selos de ❄ nos ares ligados.
- **Barra de ferramentas carregada:** nove botões no topo (*Auto/Dia/Noite, Visão noturna, Rótulos, Recentrar, Vista de cima, Pessoa, bonequinho, Fachada, Painel*). É ótimo para quem opera um prédio; **para o cliente de um apartamento é excesso**. No produto, manter só *Recentrar*, *Rótulos* e (depois) *Vista de cima*.
- **Escala do modelo:** um templo de 414 cadeiras e ~14 ambientes. Um apartamento de 45 m² é **muito mais simples** de renderizar; o orçamento de desempenho de [05](05-painel-3d-e-valor-percebido.md) tem folga.

> As capturas de tela **não** foram adicionadas ao repositório: o projeto da referência não tem licença.

## 4. O que ela mostra sobre custo (a lição central)

A referência é **uma obra de arte de engenharia para um único prédio**. O README mostra o preço disso: dezenas de iterações ajustando a posição de portas, escadas, vasos e acabamentos a partir de fotos do cliente; um documento de especificação de 26 KB (`rooms/BRIEF.md`); coordenadas medidas à mão da planta do arquiteto.

> **Isso é exatamente o que o seu briefing quer evitar** ("evitar desenvolver o painel manualmente para cada cliente"). A cena aqui é **código**, não **dados**. Para vender para N clientes, a cena precisa virar dado: *template (GLB) + manifesto de slots + vínculos*, como descrito em [05](05-painel-3d-e-valor-percebido.md).

## 5. Triagem de funcionalidades

Pergunta aplicada a cada recurso: *aumenta valor percebido? facilita a instalação? reduz custo/suporte? aumenta margem? diferencia? escala?*

| Recurso da referência | Valor percebido | Custo p/ construir | Decisão |
|---|---|---|---|
| Objeto 3D reflete o estado real (luz acende, porta abre, LED do ar) | **Alto** | Baixo–médio | **MVP** |
| Tocar no objeto alterna/abre o controle | **Alto** | Baixo | **MVP** |
| Painel com cenas ("Rotinas") e resumo (N luzes acesas) | **Alto** | Médio | **MVP** (cenas); automações no MVP 2 |
| Níveis de qualidade + render sob demanda + governador simples | **Alto** (bateria, tablets 24/7, TVs) | Médio | **MVP** (versão enxuta) |
| Câmera que voa ao ambiente / vista de cima navegável | Médio–alto | Médio | **MVP 2** (no MVP: botões de ambiente com câmera pré-definida) |
| Dia/noite e clima ao vivo | Médio (imersão) | Baixo | MVP 2 |
| Modo "Pessoa" (caminhar em 1ª pessoa, colisão, escada) | Médio (*wow* de demo) | **Alto** | Só se virar peça de venda; fora do MVP |
| Animação do ar (aleta, fluxo, tour de câmera), maçaneta e portas animadas | Baixo–médio | Médio | Depois |
| Mobiliário detalhado, logos e texturas procedurais por prédio | Baixo por casa | **Muito alto** | **Não** (usar biblioteca de assets reutilizável) |
| Cena derivada de fotos/vídeos do cliente | Alto *só para um cliente* | **Muito alto** | **Não escalável** |

## 6. Licença: o que pode e o que não pode

Sem arquivo `LICENSE`, vale o padrão legal: **todos os direitos reservados**. Portanto:

- ✅ Usar como **referência conceitual** (o que você pediu) e aprender as técnicas.
- ⛔ **Não copiar código** para o produto comercial sem **autorização expressa** do autor (LGRSV). Se houver interesse em reaproveitar o motor, peça uma licença por escrito (ou um acordo de parceria).
- A dependência de Three.js é MIT; usar Three.js é livre.

## 7. Conclusão

A referência **prova a tese de UX** (um modelo 3D vivo é mais impactante que uma lista de dispositivos) e **entrega um catálogo de técnicas de desempenho** diretamente aplicáveis. Mas o desenho *"cena em código, acoplada ao HA"* é o oposto do que o produto replicável precisa. A solução é manter as ideias, trocar o modelo de dados e o adaptador, e tornar a cena **data-driven**.
