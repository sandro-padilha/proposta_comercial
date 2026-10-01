# 08 · MVP, custos, negócio e riscos

Selos: ✅ confirmado · 🟡 provável · 🔬 necessita teste. Os **preços da Tuya e do Supabase em US$ são oficiais** ✅ (lidos nas páginas dos fornecedores em 2026-10-01); **todos os valores em R$ são premissas a validar com cotações reais** (câmbio assumido R$ 5,50/US$).

## 1. POC × MVP × Produto

| | Objetivo | Prova o quê | Tempo (1 dev, em paralelo com IA) | Custo de hardware |
|---|---|---|---|---|
| **POC** | Demonstração funcional na **sua** casa | A integração funciona; o 3D impressiona; a latência é boa | 3–5 semanas | R$ 300–600 |
| **MVP 1** | **Piloto pagante** (1–3 clientes) | Instala em ≤ 4 h; o cliente usa; ele paga | 8–12 semanas após a POC | por cliente |
| **MVP 2** | Fechadura, energia, cenas editáveis, usuários | Aumenta o ticket e a retenção | 8–10 semanas | por cliente |
| **MVP 3** | Multi-instalador, templates, onboarding, config remota | Replica sem você | 14–20 semanas | — |
| **Produto 1.0** | Vendável com suporte e termos | Opera como negócio | — | — |

### POC — a menor coisa que demonstra tudo

| Hardware | Software |
|---|---|
| 1 lâmpada Wi-Fi (Smart Life) · 1 hub IR (TV e ar) · 1 sensor (porta **ou** temperatura/umidade) · opcional: 1 tomada com medidor | Painel 3D de **1 cômodo** com 3–4 objetos · backend mínimo (`poc/tuya-core`) · integração Tuya (trial) · banco ([schema pronto e testado](06-modelo-de-dados.md)) · login básico |

Funcionalidades: ligar/desligar luz · consultar estado · enviar comando IR · consultar sensor · exibir estado no 3D · atualizar sozinho (evento Pulsar) · **voz via skill Smart Life** (sem código; mostra Alexa na demo). **Fora:** fechadura, multi-cliente, templates, edição de cenas, skill própria.

### MVP 1 — piloto pagante (começa **depois do Portão 1**)

1 template (45 m²) · 8–12 slots · console do instalador (importar, auto-match, piscar, testar, publicar) · 3 cenas fixas · 2–3 automações padrão · alertas push · barra de estado · PWA com modo lista · multi-casa com RLS · painel de saúde · termos e LGPD básicos.

### MVP 2

Fechadura (após S4) · energia por tomada e gráficos · edição de cenas/automações · papéis de usuário e convites · 3 templates · vista de cima · alertas visuais.

### MVP 3

Onboarding por QR · gerador/editor de planta · marca branca por parceiro · configuração remota · skill Alexa própria (se necessária) · **Edge Box** (se o Portão 1 ou os pilotos exigirem).

### O que precisa existir para **vender** (Produto 1.0)

Contrato e termos · política de privacidade/LGPD · garantia e RMA · catálogo homologado de dispositivos (Anatel, NF) · manual do cliente e cartão de voz · monitoramento + status page · backups testados · processo de suporte (WhatsApp + SLA) · cobrança (cartão/PIX/boleto) · exportação e encerramento (o cliente leva os dispositivos e a conta Smart Life).

## 2. Filtro dos 7 critérios

● atende · ○ em parte · (vazio) não. Colunas: 1 valor percebido · 2 facilita instalação · 3 reduz custo · 4 reduz suporte · 5 aumenta margem · 6 diferencia · 7 escala.

| Funcionalidade | 1 | 2 | 3 | 4 | 5 | 6 | 7 | Decisão |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|
| Estado real no 3D + toque para comandar | ● | | | ○ | ○ | ● | ○ | **MVP 1** |
| Barra de estado / alertas (porta, consumo) | ● | | | ● | ● | ○ | ● | **MVP 1** |
| Cenas prontas do template | ● | ● | | ● | ○ | ○ | ● | **MVP 1** |
| Console do instalador (importar, auto-match, piscar, testar) | | ● | ● | ● | ● | | ● | **MVP 1** |
| Templates de residência | ○ | ● | ● | | ● | ○ | ● | **MVP 1** |
| Multi-tenant com RLS | | | | | | | ● | **MVP 1** (barato; já pronto) |
| Alexa via skill Smart Life | ● | ● | ● | ● | | | ● | **MVP 1** (zero código) |
| IR (TV/ar) com "estado presumido" | ● | ○ | | | ○ | | ○ | **MVP 1** |
| Energia por tomada medidora | ● | ● | | | ● | ○ | ○ | **MVP 1** (1–2 tomadas) |
| Automações simples | ○ | | | ○ | ○ | | ○ | MVP 1 (3 padrão) · editor no MVP 2 |
| Fechadura | ● | ○ | | | ● | ● | | **MVP 2** (após teste do modelo) |
| Painel de saúde dos dispositivos | | | ○ | ● | ○ | | ● | MVP 1 (versão simples) |
| Vista de cima / dia-noite | ○ | | | | | ○ | | MVP 2 |
| Skill Alexa própria | ○ | | | | ○ | ○ | ○ | Fase 3, só se necessário |
| Gerador/editor de planta | ● | ● | ● | | ● | ● | ● | MVP 3 (grande alavanca de escala) |
| **Edge Box** (local/Zigbee) | ○ | | ○ | ● | ● | ○ | ● | Plano B; decidir no Portão 1 |
| Modo "Pessoa" em 1ª pessoa | ○ | | | | | ○ | | **Não** (só se virar peça de venda) |
| Animações de fluxo de ar, maçanetas | | | | | | | | **Não** |
| Fotorrealismo e modelagem por cliente | ○ | | | | | | | **Não** |
| App nativo de loja | ○ | | | | | | ○ | Depois (Capacitor sobre a PWA) |

## 3. Custos

### 3.1 Hardware (por casa)

Âncoras de varejo BR (2026) 🟡: lâmpada R$ 26–50 · hub IR R$ 40–100 · sensor de porta R$ 80–112 · tomada com medidor R$ 35–130 · Echo Dot R$ 354–429 · fechadura Wi-Fi R$ 318–1.780. Itens com `*` são **estimativas minhas**, sem âncora de busca.

| Item | Essencial (studio/1 q., 30–45 m²) | Conforto | Premium |
|---|---:|---:|---:|
| Lâmpada Wi-Fi (≈ R$ 40) | 6 → 240 | 10 → 400 | 10 → 400 |
| Hub IR Wi-Fi (≈ R$ 70) | 2 → 140 | 2 → 140 | 3 → 210 |
| Gateway Zigbee* (≈ R$ 110) | — | 1 → 110 | 1 → 110 |
| Sensor porta/janela (≈ R$ 80–90) | 1 → 90 | 3 → 240 | 3 → 240 |
| Sensor de movimento* (≈ R$ 80) | 1 → 80 | 2 → 160 | 2 → 160 |
| Sensor temp./umidade* (≈ R$ 80) | 1 → 80 | 2 → 160 | 2 → 160 |
| Tomada com medidor (≈ R$ 60) | 2 → 120 | 4 → 240 | 4 → 240 |
| Botão de cena sem fio* (≈ R$ 50) | — | 3 → 150 | 3 → 150 |
| Echo Dot (opcional, ≈ R$ 400) | — | 1 → 400 | 1 → 400 |
| Fechadura Wi-Fi (≈ R$ 900) | — | — | 900 |
| Medidor de circuito* (≈ R$ 300; **eletricista**) | — | — | 300 |
| Tablet de parede (≈ R$ 700) | — | — | 700 |
| **Total** | **≈ R$ 750** | **≈ R$ 2.000** | **≈ R$ 3.970** |

### 3.2 Plataforma (mensal)

| Item | POC | MVP/piloto (≤ 10 casas) | 100 casas | 1.000 casas |
|---|---:|---:|---:|---:|
| Frontend (Cloudflare Pages) | R$ 0 | R$ 0 | R$ 0–30 | R$ 30–150 |
| Supabase (Pro US$ 25: 100 mil MAU, 8 GB, 500 conexões Realtime) | R$ 0 (free) | ≈ R$ 140 | R$ 140–350 | R$ 700–1.500 |
| Core (Fly.io/VPS, US$ 5–15) | R$ 0–30 | R$ 30–85 | R$ 85–200 | R$ 300–800 |
| Domínio, e-mail transacional, Sentry, push | ≈ R$ 5 | ≈ R$ 20–60 | R$ 60–150 | R$ 200–500 |
| Alexa (skill própria: conta de dev e Lambda/endpoint) | — | R$ 0 | R$ 0–20 | R$ 20–100 |
| App de loja (opcional): Apple US$ 99/ano · Google US$ 25 único | — | — | — | — |
| **Subtotal (sem Tuya)** | **≈ R$ 0–40** | **≈ R$ 200–300** | **≈ R$ 400–700** | **≈ R$ 1,3–3 mil** |
| **Por casa** | — | R$ 20–30 | **≈ R$ 5** | **≈ R$ 2–3** |
| **Tuya** | Trial (R$ 0; **só a sua casa**) | **Flagship US$ 25 mil/ano ≈ R$ 11,5 mil/mês** ✅ ou plano negociado | idem | idem |

### 3.3 Taxa fixa da Tuya diluída (R$/casa/mês)

**Preços de tabela oficiais** ✅: US$ 5 mil = app próprio (1º ano) · US$ 25 mil = IoT Core Flagship · US$ 50 mil = Corporate. **Atenção:** o app próprio **não substitui** o IoT Core se o servidor usar a Open API; nesse caso os custos **somam**.

| Taxa anual | 10 casas | 50 | 100 | 500 | 1.000 | 2.000 |
|---|---:|---:|---:|---:|---:|---:|
| US$ 5.000 (R$ 27.500/ano) | 229,2 | 45,8 | 22,9 | 4,6 | 2,3 | 1,1 |
| US$ 25.000 (R$ 137.500/ano) | 1.145,8 | 229,2 | 114,6 | 22,9 | 11,5 | 5,7 |
| US$ 50.000 (R$ 275.000/ano) | 2.291,7 | 458,3 | 229,2 | 45,8 | 22,9 | 11,5 |

**Ponto de equilíbrio** para manter a Tuya ≤ R$ 10/casa/mês: **≈ 230 casas** (US$ 5 mil) · **≈ 1.150** (US$ 25 mil) · **≈ 2.300** (US$ 50 mil). Se forem necessários **App SDK + IoT Core** (US$ 30 mil no 1º ano, US$ 27 mil depois): **≈ 1.375** casas no 1º ano.

Além da taxa fixa: o **excedente** custa US$ 3,15/M chamadas e US$ 1,24/M mensagens ✅; uma tomada com medidor reportando a cada 10 s gera ~259 mil mensagens/mês (≈ US$ 0,32/mês), irrelevante frente à taxa fixa, mas decisiva no Trial.

### 3.4 Esforço de desenvolvimento (pessoa-semanas; 1 dev sênior full-stack com apoio de IA)

| Entrega | Estimativa | Observação |
|---|---:|---|
| Spikes S1–S7 | 1 | Inclui e-mail à Tuya |
| POC | 3–5 | `poc/tuya-core` e schema já prontos e testados |
| MVP 1 | 8–12 | Painel + core + console do instalador + 1 template |
| MVP 2 | 8–10 | Fechadura, energia, editor de cenas, papéis |
| MVP 3 | 14–20 | Gerador de planta é a parte grande |
| Skill Alexa própria | 4–6 | + OAuth + certificação (prazo 🔬) |
| Edge Box (plano B) | 10–16 | Zigbee + LAN + atualização remota |
| App próprio (Arquitetura D) | 10–16 🔬 | App híbrido + ponte WebView↔SDK; **estimativa minha**, depende do SDK |
| Arte 3D (3 templates) | 6–10 dias de artista | R$ 1,5–4 mil por template 🟡 |

### 3.5 Operação 🟡

Suporte: **≈ 2 h/casa no 1º mês**, depois ≈ 10 min/casa/mês (hipótese). Visitas técnicas: meta ≤ 1 por 10 casas/ano. Peças de reposição: reservar ≈ 3 % do hardware vendido.

## 4. Economia por casa (hipótese a validar)

### 4.1 Venda inicial (instalação premium com 3D)

Preço-hipótese: custo = hardware + instalação (R$ 100/h) + 3D/projeto + deslocamento + taxas 4 %.

| Pacote | Preço | Hardware | Instalação | 3D/projeto | Desloc. | Taxas | **Margem** |
|---|---:|---:|---:|---:|---:|---:|---:|
| Essencial | R$ 2.500 | 750 | 400 (4 h) | 150 | 80 | 100 | **R$ 1.020 (41 %)** |
| Conforto | R$ 5.200 | 2.000 | 600 (6 h) | 200 | 80 | 208 | **R$ 2.112 (41 %)** |
| Premium | R$ 9.900 | 3.970 | 900 (9 h) | 300 | 100 | 396 | **R$ 4.234 (43 %)** |

Lição: **hardware é repasse** (varejo é competitivo); a margem vem de **instalação + personalização 3D + assinatura**. Vender "só o kit" não fecha conta.

### 4.2 Assinatura (R$ 39/mês — hipótese) — contribuição mensal por casa

R$ 39 − taxas 4 % (R$ 1,56) − infra (≈ R$ 4 a ~100 casas) − suporte (≈ 10 min × R$ 60/h ≈ R$ 9) − **taxa Tuya por casa**:

| Taxa Tuya por casa | Contribuição | % |
|---|---:|---:|
| R$ 0 (acordo/incluída, ou Edge local) | **R$ 24,4** | 63 % |
| R$ 10 | R$ 14,4 | 37 % |
| R$ 23 (US$ 25 mil com 500 casas) | R$ 1,4 | 4 % |
| R$ 46 (US$ 50 mil com 500 casas, ou US$ 25 mil com ~250) | **negativa** | — |

**É por isso que o custo da nuvem da Tuya é o Portão 1**: com a taxa de tabela (US$ 25 mil/ano) e menos de ~1.000 casas, a assinatura não paga a própria infraestrutura.

## 5. Modelo de negócio

| Modelo | Barreira de compra | Velocidade de caixa | Margem | Escala | Risco |
|---|---|---|---|---|---|
| **Kit + instalação + 3D (pontual)** | Média (ticket R$ 2,5–10 mil) | **Alta** (sinal de 50 %) | Boa (≈ 41 %) | Limitada pela sua agenda | Baixo |
| Kit + mensalidade (nuvem + suporte) | Menor (entrada baixa) | Baixa (hardware no seu caixa) | Cresce com o tempo | Boa | Capital de giro; custo da nuvem |
| Instalação premium (hardware + obra + 3D) | Alta | Alta | **Melhor por projeto** | Baixa | Dependência de pessoas |
| **Licenciamento para instaladores (marca branca)** | Baixa para o instalador | Média | **Alta** (software) | **Alta** | Exige plataforma estável e playbook de suporte |
| Só kit (varejo) | Baixa | Média | **Fraca** | Média | Compete com marketplace |

### Recomendação (em fases)

1. **Agora — caixa:** *instalação premium com 3D* em **preço fechado**, **50 % de sinal**, assinatura **opcional** nos primeiros pilotos (12 meses incluídos em Conforto/Premium). Quem paga o hardware é o sinal do cliente, não o seu capital.
2. **Após o Portão 1:** assinatura passa a **padrão** (R$ 29–49/mês ou anual R$ 299–449), dimensionada pela taxa real da nuvem.
3. **Após ~5 casas estáveis:** **licenciar para instaladores** (marca branca): taxa de adesão + R$ 9–15 por casa ativa/mês (hipótese). É aqui que a plataforma, e não a sua agenda, vira o ativo. **Cuidado:** a licença da Tuya é **não sublicenciável** ✅; a marca branca exige **ordem de serviço** que a permita ou **um projeto Tuya por parceiro**.

### Onde vender primeiro (validar 2 nichos em paralelo)

| Nicho | Por que | Cuidado |
|---|---|---|
| **Anfitriões de aluguel por temporada** | Ar desligado no *check-out*, consumo, check-in remoto: **retorno mensurável** | Fechadura vira requisito; o 3D vale menos que a economia |
| **Decorados e investidores de construtoras** | O 3D da planta é peça de **marketing** da venda do imóvel | Ciclo de venda longo |
| **Arquitetos/decoradores** | Indicam e já têm a planta (insumo do template) | Comissão de indicação |
| Clientes de alto padrão compactos | Pagam pela experiência | Expectativa visual alta |

## 6. Cronograma realista

| Semana | Foco | Saída esperada |
|---|---|---|
| **0** (3–5 dias) | Spikes S1–S7; e-mail à Tuya | S1–S3 funcionando; resposta da Tuya em andamento |
| **1–2** | **POC**: 3D (1 cômodo, 3 objetos) + `tuya-core` com dispositivos reais + banco | Demo ao vivo (vídeo): lâmpada, IR e sensor refletidos no 3D em < 2 s |
| **3–4** | Backend mínimo: auth, `issue_command`, worker Pulsar, Realtime; console do instalador v0 | Painel logado, no celular, com 1 casa |
| **5–6** | **1º apartamento funcional** (o seu ou de um amigo): template 45 m², cenas, alertas, PWA | 7 dias sem intervenção manual |
| **7** | **Teste com usuários reais** (3–5) + 10 demos a prospects (H1, H2) | Relatório de UX e de preço |
| **8** | **Portão 1** (resposta Tuya) → decidir B × C; **Portão 2** (demanda) | Decisão documentada |
| **9–16** | **Piloto pagante** em 1–3 clientes (+ fechadura/energia se S4 ok) | NPS ≥ 8; instalação ≤ 4 h; ≤ 1 chamado/casa/mês |
| **17+** | MVP 3: onboarding, gerador de planta, multi-instalador | — |

Premissas de prazo: 1 dev com apoio de IA; **não** inclui skill Alexa própria (+4–6 semanas e certificação com prazo desconhecido) nem Edge Box (+10–16). O gargalo previsível é o **template 3D** (arte) e o **modelo de fechadura**.

## 7. Riscos (priorizados)

| # | Risco | Prob. | Impacto | Mitigação | Sinal precoce |
|---|---|:-:|:-:|---|---|
| 1 | **Custo da nuvem Tuya** inviabiliza a assinatura: **Flagship US$ 25 mil/ano** ✅; o Trial **proíbe uso comercial** ✅ | **Alta** | **Crítico** | Portão 1; `ProviderAdapter`; plano B **Edge Zigbee (E)** ou **app próprio (B/D)**; plano negociado | Resposta da Tuya; qualquer cliente antes do acordo |
| 2 | **Contrato Tuya**: licença **não sublicenciável**, vedações 3-ix/3-xi, **suspensão sem aviso**, responsabilidade limitada a US$ 5 mil, foro da Califórnia ✅ | Média–alta | **Crítico** | **Ordem de serviço escrita** que permita atender terceiros; plano B pronto; Alexa/Smart Life seguem independentes; ensaio de contingência | Cláusulas recusadas; avisos de suspensão |
| 3 | **Limite de 4 comandos/s por projeto** ✅ trava cenas em muitas casas | Média | Alto | Fila com *token bucket*; cenas nativas; *jitter* em automações; Edge; pedir limite maior ([03](03-arquitetura-e-stack.md) §5.1) | Erros 1110/1199; fila > 10 s |
| 4 | **Mudança de regras/cotas/data center** da Tuya (houve migração do Brasil para *Eastern America* em 2025-11-25 ✅) | Média | Alto | Evento em vez de polling; configurar data center por casa; monitorar avisos | Dispositivos sumindo da lista; erro 2007 |
| 5 | **Fechadura**: serviço separado, firmware sem chave em nuvem (DP 49/50), falha de segurança ou responsabilidade civil | Média | Alto | Teste por modelo (S4); `can_unlock` + PIN + auditoria; sem fail-open; termo; seguro | S4 falha |
| 6 | **Custo do 3D por cliente** explode | Média | Alto | Templates + gerador; orçamentos de desempenho; "sob medida" cobrado à parte | Horas de arte por casa > 2 |
| 7 | **Suporte** (Wi-Fi, firmware, bateria) consome a margem | **Alta** | Médio–alto | Catálogo homologado; Zigbee-first; painel de saúde; guia do roteador | > 1 chamado/casa/mês |
| 8 | **Regulatório**: Anatel, INMETRO, NBR 5410, LGPD (a Tuya exige que **você** responda pela privacidade ✅) | Média | Alto | Fornecedores nacionais com NF; sem obra em quadro sem eletricista; advogado; política de privacidade | Produto sem selo no catálogo |
| 9 | **Diferencial fraco** (SmartThings já inclui Map View 3D no app; apps de fabricantes) | Média | Alto | Posicionar a **entrega completa** (instalação + 3D personalizado + pt-BR + Alexa); medir H1–H3 | H1 < 3/10 |
| 10 | **Desempenho** em celulares fracos/TVs | Média | Médio | Orçamentos, modo lista, S6 | FPS < 30 no aparelho-alvo |
| 11 | **Segurança/privacidade** (vazamento de presença, comandos indevidos) | Baixa–média | Alto | RLS, MFA, auditoria, retenção; teste de invasão antes do 1.0 | — |
| 12 | **Add-on Alexa próprio**: certificação (prazo não publicado), OAuth e exigência de dispositivo online 24/7 no teste | Média | Médio | Usar Smart Life no MVP; só construir se necessário | Pedido de "cenas por voz" |
| 13 | **Pessoa-chave / equipe pequena** | Média | Médio | Documentação, testes, ADRs (já iniciados) | — |
| 14 | **Caixa**: capital de giro em hardware | Média | Médio | Sinal de 50 %; compra sob demanda | Pedidos antes do sinal |
| 15 | **Licença da referência**: reaproveitar código sem permissão | Baixa | Médio | Reuso só com licença do autor ([02](02-referencia-igreja-3d.md)) | — |

## 8. Resposta à pergunta central

> **É tecnicamente e comercialmente viável criar uma solução de automação residencial acessível, sem Home Assistant, com dispositivos de baixo custo (Tuya/Alexa) e interface 3D personalizada como diferencial?**

**Sim — com uma condição bloqueante e quatro correções de premissa.**

- **Tecnicamente: sim, com alta confiança.** Cada peça foi **verificada**: assinatura, token e Pulsar da Tuya compatíveis byte a byte com o SDK oficial e com a doc oficial (27 testes); IR, status e eventos mapeados em fonte primária; modelo multi-tenant com 50 asserções em PostgreSQL 16; stack 3D madura (`extras` do glTF → `userData` confirmado no código do Three.js; `frameloop="demand"` confirmado no R3F). **Ainda falta** uma chamada real à Tuya (S1).
- **Comercialmente: sim, se** o acesso comercial à nuvem da Tuya couber (≤ ~R$ 10 por casa/mês) **e** o contrato permitir atender terceiros, **ou** se adotarmos o plano B. **Fatos oficiais ✅:** o Trial (50 dispositivos / 10 controláveis) é **só para depuração e proíbe uso comercial**; a edição comercial mínima, **Flagship, custa US$ 25 mil/ano**; o app próprio custa US$ 5 mil + US$ 2 mil/ano mas **não dá acesso à Open API**; a licença é **não sublicenciável** e a Tuya limita o envio de comandos a **4/s por projeto**. Sem acordo, a assinatura só fecha acima de ~1.000 casas.

**Premissas a alterar:**

1. ~~"Tuya Cloud como backbone para todos os clientes desde o dia 1."~~ → **Tuya Cloud (Trial) só no POC, na sua casa**; **Portão 1** (preço **e** contrato) antes de qualquer cliente, mesmo pago; **plano B** pronto no desenho: **Edge Zigbee** (independente da nuvem) ou **app próprio**. Nota: o controle LAN de dispositivos Wi-Fi **não** elimina a Tuya, pois a `local_key` vem da conta de nuvem.
2. ~~"3D é o diferencial."~~ → o diferencial é a **entrega completa**: **3D do apê do cliente + instalação + suporte pt-BR + voz + preço**. A Samsung já inclui um Map View 3D no app SmartThings.
3. ~~"Alexa como parte da arquitetura."~~ → Alexa é **voz paralela** (skill Smart Life), não backend nem fonte de eventos; skill própria só na Fase 3.
4. ~~"Plug-and-play total."~~ → **assistido** no MVP (importação + auto-match + piscar); autoatendimento só com App SDK/QR.

**Resumo executivo das respostas pedidas**

| Pergunta | Resposta |
|---|---|
| Qual arquitetura? | **B no POC, com costuras de C e D**: PWA 3D → Supabase + Core Node → `ProviderAdapter` (Tuya primeiro; Edge ou app próprio conforme o Portão 1). [03](03-arquitetura-e-stack.md) |
| Qual stack? | React 19 + R3F/Three.js + Vite + PWA · Node 22/Fastify · Supabase (SP) · Cloudflare Pages · Fly.io/VPS |
| Qual MVP? | POC (1 cômodo, 3 dispositivos, voz Smart Life) → MVP 1 pagante após o Portão 1 |
| Qual hardware? | Lâmpadas Wi-Fi, hub IR, sensores **Zigbee** com gateway, tomadas com medidor; fechadura só no MVP 2 após teste do modelo |
| Qual modelo de implantação? | Assistido por console do instalador, templates e auto-match; ≤ 4 h por apê |
| Qual modelo de negócio? | Instalação premium com 3D e sinal de 50 % → assinatura após o Portão 1 → licença para instaladores |
| Maiores riscos? | **Custo e contrato da Tuya** (US$ 25 mil/ano, não sublicenciável, suspensão sem aviso), limite de 4 comandos/s, fechadura, custo do 3D por cliente, suporte, diferencial vs. SmartThings, regulatório |

## 9. Próximos 14 dias

1. **Enviar o e-mail à Tuya** para **vip@tuya.com** (modelo em [01](01-evidencias-e-pesquisa.md) §7): preço/plano para integrador, **ordem de serviço** que permita atender terceiros, limite de comandos, data center do Brasil, fechaduras e IR, *Smart Voice*.
2. **S1, S1b e S2** com `poc/tuya-core` (conta *Smart Home*, data center, vínculo, lâmpada, IR, evento, teste de *throttling*) — dentro do Trial, **na sua casa**.
3. **S3** (sensores/energia) e **S5** (Alexa/Smart Life), **S6** (GLB de teste em 3–4 aparelhos).
4. **Escolher o apê-piloto** e 10 prospects para as demos (H1/H2); definir os 2 nichos. **Sem cobrar ninguém antes do Portão 1.**
5. **Cotar** hardware (3 fornecedores nacionais com NF) e **modelagem 3D** do 1º template.
6. Avaliar em paralelo o **App SDK em edição de desenvolvimento (grátis)**: um app de teste com a ponte WebView↔SDK mostra se a **Arquitetura D** é viável 🔬.
