# Casa 3D — viabilidade, arquitetura e plano de MVP

Estudo técnico e comercial de um produto de automação residencial acessível, **sem Home Assistant**, com **painel 3D personalizado**, dispositivos **Tuya/Smart Life** e **Alexa**. Data: 2026-10-01. Estado: **estudo + blocos de código verificados** (ainda não há produto).

## Resposta objetiva

**É viável? Sim — com uma condição bloqueante e quatro correções de premissa.**

- **Tecnicamente: sim, alta confiança.** Cada peça foi verificada: assinatura/token/Pulsar da Tuya idênticos ao SDK oficial (22 testes), rotas de IR/sensores mapeadas em código aberto, modelo multi-tenant testado em PostgreSQL 16 (50 asserções), stack 3D madura.
- **Comercialmente: sim, se o acesso comercial à nuvem da Tuya couber.** O trial gratuito não sustenta nem um piloto de 3 casas (50 dispositivos conectados / 10 controláveis 🟡), e as edições comerciais foram relatadas em **US$ 25–50 mil/ano** 🟡 (2022, comunidade; **preço atual não confirmado** — o site da Tuya está bloqueado nesta sessão). Sem acordo, a assinatura só fecha acima de ~1.000 casas. O plano B existe e está previsto no desenho (integração local: Zigbee + LAN).

| Sua hipótese | O que mudou |
|---|---|
| Tuya Cloud como backbone de todos os clientes desde o dia 1 | **Só no POC e na 1ª casa.** Portão 1 (custo/termos) antes de qualquer piloto pago; `ProviderAdapter` mantém o plano B aberto |
| O painel 3D é o diferencial | **O 3D sozinho não é raro:** a Samsung já inclui um *Map View 3D* no app SmartThings. O diferencial é a **entrega completa** (3D do apê do cliente + instalação + suporte pt-BR + voz + preço) |
| Alexa faz parte da arquitetura | **Voz paralela** (skill Smart Life, zero código). Não é backend nem fonte de eventos; skill própria só na Fase 3 |
| Plug-and-play total | **Assistido** no MVP (importação + auto-match + "piscar para identificar", ≤ 4 h); autoatendimento só com App SDK/QR |

## Arquitetura recomendada (B com costuras de C)

```text
 PAINEL 3D (PWA · React + R3F) ──HTTPS/WSS──► SUPABASE (Postgres + Auth + Realtime + Storage, RLS)
                                                    ▲
                                                    │ service_role
                                         CORE (Node/Fastify): comandos · cenas · automações · alertas
                                                    │
                                          ProviderAdapter ──► TuyaCloud (MVP) · Edge local (plano B)
                                                    │
                                              TUYA CLOUD ◄──► dispositivos
        ALEXA ──(skill Smart Life, nuvem↔nuvem)──► TUYA   ← caminho paralelo: voz funciona mesmo sem o nosso servidor
```

## Decisão em portões

| Portão | Pergunta | Evidência | Se falhar |
|---|---|---|---|
| **0 · Spikes** (sem. 0) | A tecnologia funciona com dispositivos reais? | S1–S3 ([01](docs/01-evidencias-e-pesquisa.md)) | Trocar dispositivos/ajustar desenho |
| **1 · Nuvem** (sem. 8) | Custo e termos da Tuya cabem? | Proposta escrita ≤ ~R$ 10/casa/mês | **Plano B:** Edge (Zigbee+LAN) ou App SDK |
| **2 · Demanda** (sem. 7–8) | Pagam pelo 3D? | ≥ 3 de 10 aceitam +R$ 500; 1–3 pré-vendas com sinal | Reposicionar (aluguel/energia), simplificar o 3D |
| **3 · Piloto** (sem. 16) | Opera com margem? | Instalação ≤ 4 h; ≤ 1 chamado/casa/mês; margem ≥ 40 % | Ajustar preço/escopo |

## Mapa do repositório

| Caminho | Conteúdo |
|---|---|
| [`docs/01-evidencias-e-pesquisa.md`](docs/01-evidencias-e-pesquisa.md) | **Confirmado / Provável / Necessita teste / Não recomendado** para cada afirmação; fontes; spikes; e-mail para a Tuya |
| [`docs/02-referencia-igreja-3d.md`](docs/02-referencia-igreja-3d.md) | Análise crítica da referência (`LGRSV/igreja-3d-v1`): o que aproveitar, o que evitar, licença |
| [`docs/03-arquitetura-e-stack.md`](docs/03-arquitetura-e-stack.md) | Arquiteturas A/B/C comparadas, recomendação, fluxos, stack, estrutura do projeto, confiabilidade, segurança |
| [`docs/04-integracao-tuya-e-alexa.md`](docs/04-integracao-tuya-e-alexa.md) | Rotas Tuya, passo a passo, mapa DP→capacidade, IR, fechadura, Alexa |
| [`docs/05-painel-3d-e-valor-percebido.md`](docs/05-painel-3d-e-valor-percebido.md) | Tecnologia 3D, plataformas, pipeline de modelos, manifesto/vínculos, valor percebido |
| [`docs/06-modelo-de-dados.md`](docs/06-modelo-de-dados.md) | Banco, entidades, multi-tenant/RLS, escala |
| [`docs/07-plug-and-play-e-instalacao.md`](docs/07-plug-and-play-e-instalacao.md) | Níveis de plug-and-play, auto-match, console do instalador, tempo de instalação, suporte, conformidade |
| [`docs/08-mvp-custos-negocio-riscos.md`](docs/08-mvp-custos-negocio-riscos.md) | POC/MVP/produto, custos, economia por casa, modelo de negócio, cronograma, riscos, **resposta final** |
| [`database/schema.sql`](database/schema.sql) · [`database/tests/`](database/tests/) | Schema multi-tenant com RLS (23 tabelas) e **50 testes** em PostgreSQL 16 |
| [`poc/tuya-core/`](poc/tuya-core/) | Cliente Tuya (assinatura, token, comandos, IR) e consumidor Pulsar em TypeScript, **22 testes** contra o SDK Python oficial |

### Rodar as verificações

```bash
# Tuya: assinatura/Pulsar idênticos ao SDK oficial (Node >= 22.18)
cd poc/tuya-core && npm install && npm test && npm run typecheck

# Banco: sobe um PostgreSQL temporário, aplica o schema e testa isolamento/permissões
bash database/tests/run.sh
```

## O que está verificado e o que não está

- ✅ **Verificado por execução:** os 22 testes do POC (inclui paridade com o SDK Python oficial) e os 50 do schema.
- ✅ **Verificado por leitura de código-fonte:** SDKs oficiais da Tuya (Python e Node), integração do Home Assistant, integração open-source de IR, `GLTFLoader` do Three.js e tipos do R3F.
- 🟡 **Não verificado nas páginas oficiais** (bloqueadas na rede desta sessão: `developer.tuya.com`, `support.tuya.com`, `tuya.com`, `developer.amazon.com`, `supabase.com`, `www.home-assistant.io`, `community.home-assistant.io`, `apis.io`, `lgrsv.github.io`): **preços e cotas da Tuya**, detalhes da Alexa, preços do Supabase. Estão marcados como 🟡 e listados em [01](docs/01-evidencias-e-pesquisa.md). Para destravar: menu do ambiente na barra de título da sessão → *Edit* → *Network access*.
- 🔬 **Nenhuma chamada real à Tuya foi feita** (não há credenciais). Os testes provam que o código gera **exatamente** o que o SDK oficial gera, não que uma conta específica será aceita.
- 💰 **Todos os valores em R$ são premissas** (câmbio R$ 5,50/US$; âncoras de varejo de 2026 de anúncios). Cotar antes de decidir.

## Próximos passos

1. Liberar os hosts bloqueados para **confirmar** os pontos 🟡 (principalmente a Tuya).
2. **Enviar o e-mail à Tuya** (modelo em [01](docs/01-evidencias-e-pesquisa.md) §5).
3. Rodar os **spikes S1–S3** com `poc/tuya-core` (conta, projeto, lâmpada, IR, sensor, evento).
4. Montar o **POC visual** (1 cômodo, 3 objetos) sobre o schema e o cliente já prontos.

Lista completa de 14 dias em [08](docs/08-mvp-custos-negocio-riscos.md) §9.
