# Casa 3D — viabilidade, arquitetura e plano de MVP

Estudo técnico e comercial de um produto de automação residencial acessível, **sem Home Assistant**, com **painel 3D personalizado**, dispositivos **Tuya/Smart Life** e **Alexa**. Data: 2026-10-01 (revisado após a liberação de rede, com leitura das páginas oficiais). Estado: **estudo + blocos de código verificados** (ainda não há produto).

## Resposta objetiva

**É viável? Sim — com uma condição bloqueante e quatro correções de premissa.**

- **Tecnicamente: sim, alta confiança.** Cada peça foi verificada: assinatura, token e Pulsar da Tuya idênticos ao SDK oficial e à doc oficial (27 testes), rotas de IR/sensores/eventos mapeadas em fonte primária, modelo multi-tenant testado em PostgreSQL 16 (50 asserções), stack 3D madura.
- **Comercialmente: sim, se o acesso comercial à nuvem da Tuya couber.** Fatos **oficiais** ✅ (páginas lidas em 2026-10-01):
  - o **Trial** (50 dispositivos / 10 controláveis) é **só para depuração e proíbe uso comercial**;
  - a edição comercial mínima, **IoT Core Flagship, custa US$ 25 mil/ano** (Corporate, US$ 50 mil);
  - o **app próprio** custa US$ 5 mil no 1º ano e US$ 2 mil depois, mas a cota dele **não cobre a Open API** (essa exige o IoT Core);
  - a licença é **não sublicenciável**, a Tuya pode **suspender sem aviso** e limita o envio de comandos a **4/s por projeto**.

  Sem acordo, a assinatura só fecha acima de ~1.000 casas. O plano B está no desenho: **Edge Zigbee** (independente da nuvem) ou **app próprio**.

| Sua hipótese | O que mudou |
|---|---|
| Tuya Cloud como backbone de todos os clientes desde o dia 1 | **Trial só no POC, na sua casa.** O **Portão 1** (preço **e** contrato) vem antes de qualquer cliente, mesmo pago; `ProviderAdapter` mantém o plano B aberto |
| O painel 3D é o diferencial | **O 3D sozinho não é raro:** a Samsung já inclui um *Map View 3D* no app SmartThings. O diferencial é a **entrega completa** (3D do apê do cliente + instalação + suporte pt-BR + voz + preço) |
| Alexa faz parte da arquitetura | **Voz paralela** (skill Smart Life, zero código). Não é backend nem fonte de eventos; add-on próprio só na Fase 3 |
| Plug-and-play total | **Assistido** no MVP (importação + auto-match + "piscar para identificar", ≤ 4 h); autoatendimento só com app próprio (App SDK) |

## Arquitetura recomendada (B no POC, com costuras de C e D)

```text
 PAINEL 3D (PWA · React + R3F) ──HTTPS/WSS──► SUPABASE (Postgres + Auth + Realtime + Storage, RLS)
                                                    ▲
                                                    │ service_role
                                         CORE (Node/Fastify): comandos · cenas · automações · alertas
                                                    │
                                          ProviderAdapter ──► TuyaCloud (POC) · Edge Zigbee/LAN (C) · app próprio (D)
                                                    │
                                              TUYA CLOUD ◄──► dispositivos
        ALEXA ──(skill Smart Life, nuvem↔nuvem)──► TUYA   ← caminho paralelo: voz funciona mesmo sem o nosso servidor
```

## Decisão em portões

| Portão | Pergunta | Evidência | Se falhar |
|---|---|---|---|
| **0 · Spikes** (sem. 0) | A tecnologia funciona com dispositivos reais? | S1–S3 ([01](docs/01-evidencias-e-pesquisa.md)) | Trocar dispositivos/ajustar desenho |
| **1 · Nuvem** (sem. 8) | Custo **e contrato** da Tuya cabem? | Proposta escrita ≤ ~R$ 10/casa/mês **e** ordem de serviço que permita atender terceiros | **Plano B:** Edge Zigbee (C) ou app próprio (D) |
| **2 · Demanda** (sem. 7–8) | Pagam pelo 3D? | ≥ 3 de 10 aceitam +R$ 500; 1–3 pré-vendas com sinal | Reposicionar (aluguel/energia), simplificar o 3D |
| **3 · Piloto** (sem. 16) | Opera com margem? | Instalação ≤ 4 h; ≤ 1 chamado/casa/mês; margem ≥ 40 % | Ajustar preço/escopo |

## Mapa do repositório

| Caminho | Conteúdo |
|---|---|
| [`docs/01-evidencias-e-pesquisa.md`](docs/01-evidencias-e-pesquisa.md) | **Confirmado / Provável / Necessita teste / Não recomendado** para cada afirmação; fontes e datas; spikes; e-mail para a Tuya |
| [`docs/02-referencia-igreja-3d.md`](docs/02-referencia-igreja-3d.md) | Análise crítica da referência (`LGRSV/igreja-3d-v1`): o que aproveitar, o que evitar, licença |
| [`docs/03-arquitetura-e-stack.md`](docs/03-arquitetura-e-stack.md) | Arquiteturas A/B/C/D comparadas, recomendação, fluxos, **limite de 4 comandos/s**, stack, estrutura do projeto, confiabilidade, segurança |
| [`docs/04-integracao-tuya-e-alexa.md`](docs/04-integracao-tuya-e-alexa.md) | Rotas Tuya, passo a passo, mapa DP→capacidade, IR, fechadura, **custos e contrato oficiais**, Alexa |
| [`docs/05-painel-3d-e-valor-percebido.md`](docs/05-painel-3d-e-valor-percebido.md) | Tecnologia 3D, plataformas, pipeline de modelos, manifesto/vínculos, valor percebido |
| [`docs/06-modelo-de-dados.md`](docs/06-modelo-de-dados.md) | Banco, entidades, multi-tenant/RLS, escala |
| [`docs/07-plug-and-play-e-instalacao.md`](docs/07-plug-and-play-e-instalacao.md) | Níveis de plug-and-play, auto-match, console do instalador, tempo de instalação, suporte, conformidade |
| [`docs/08-mvp-custos-negocio-riscos.md`](docs/08-mvp-custos-negocio-riscos.md) | POC/MVP/produto, custos, economia por casa, modelo de negócio, cronograma, riscos, **resposta final** |
| [`database/schema.sql`](database/schema.sql) · [`database/tests/`](database/tests/) | Schema multi-tenant com RLS (23 tabelas) e **50 testes** em PostgreSQL 16 |
| [`poc/tuya-core/`](poc/tuya-core/) | Cliente Tuya (assinatura, token, comandos, IR) e consumidor Pulsar em TypeScript, **27 testes** |

### Rodar as verificações

```bash
# Tuya: assinatura/Pulsar idênticos ao SDK oficial (Node >= 22.18)
cd poc/tuya-core && npm install && npm test && npm run typecheck

# Banco: sobe um PostgreSQL temporário, aplica o schema e testa isolamento/permissões
bash database/tests/run.sh
```

## O que está verificado e o que não está

- ✅ **Por execução:** os 27 testes do POC (inclui paridade com o SDK Python oficial) e as 50 asserções do schema.
- ✅ **Por leitura de fonte primária:** páginas oficiais da **Tuya** (preços, contrato, limites, data centers, Message Service, vínculo de contas, códigos de erro), da **Amazon** (idiomas, certificação) e do **Supabase** (preços, regiões, Realtime); SDKs oficiais da Tuya; integração do HA; integração open-source de IR; `GLTFLoader` do Three.js; tipos do R3F.
- 🔬 **Nenhuma chamada real à Tuya foi feita** (não há credenciais): os testes provam que o código gera o que o SDK oficial gera, não que uma conta específica será aceita.
- ❓ **Ainda não verificado:** preço e condições das APIs *Smart Lock Open APIs* e *IR Control Hub* (exigem login); prazo de certificação do add-on Alexa; se o app Smart Life brasileiro está no *Eastern America*; a rota de comandos (duas candidatas); o endpoint WebSocket do *Eastern America*.
- 💰 **Valores em R$ são premissas** (câmbio R$ 5,50/US$; âncoras de varejo de 2026 de anúncios). Cotar antes de decidir. Os valores em US$ da Tuya e do Supabase são oficiais.

## Próximos passos

1. **Enviar o e-mail à Tuya** (vip@tuya.com; modelo em [01](docs/01-evidencias-e-pesquisa.md) §7): plano para integrador, **ordem de serviço** que permita atender terceiros, limite de comandos, data center, fechaduras, IR e *Smart Voice*.
2. Rodar os **spikes S1–S3 e S1b** com `poc/tuya-core`, **na sua casa** (Trial): conta *Smart Home*, data center, lâmpada, IR, sensor, evento, *throttling*.
3. Montar o **POC visual** (1 cômodo, 3 objetos) sobre o schema e o cliente já prontos.
4. Avaliar o **App SDK em edição de desenvolvimento (grátis)** para testar a Arquitetura D.

Lista completa de 14 dias em [08](docs/08-mvp-custos-negocio-riscos.md) §9.
