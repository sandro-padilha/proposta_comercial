# tuya-core (POC)

Blocos de integração com a **Tuya Cloud**, escritos em TypeScript e **validados contra o SDK Python oficial** (`tuya-connector-python` 0.1.2). Servem de base para o `TuyaCloudAdapter` descrito em [`docs/03`](../../docs/03-arquitetura-e-stack.md) e [`docs/04`](../../docs/04-integracao-tuya-e-alexa.md).

| Arquivo | O que faz |
|---|---|
| `src/sign.ts` | Assinatura HMAC-SHA256 da Open API (`MÉTODO \n SHA256(corpo) \n \n URL`, query ordenada) |
| `src/client.ts` | `TuyaClient`: token com cache, refresh e *single-flight*; `getStatus`, `getSpecification`, `sendCommands`; IR (`acScene`, `irKeys`, `irKey`); `TuyaApiError` |
| `src/pulsar.ts` | `PulsarConsumer`: Message Service (Pulsar sobre WebSocket): handshake, decriptação AES-128-ECB, ACK, *ping/pong*, reconexão com backoff |

## Requisitos e testes

Node **≥ 22.18** (executa `.ts` diretamente).

```bash
npm install
npm test            # 22 testes
npm run typecheck   # tsc --noEmit
```

Os testes provam:

- **Assinatura** idêntica à do SDK oficial em 5 casos (token, status, query desordenada, POST com corpo, IR).
- **Senha, URL e decriptação do Pulsar** idênticas às do SDK.
- **Consumidor**: valida cabeçalhos no handshake, entrega o evento, faz ACK e **reconecta** após queda (contra um servidor WebSocket simulado).
- **Cliente** (com `fetch` falso): token reutilizado, refresh perto da expiração, **o corpo enviado é o corpo assinado**, erro tipado, nova tentativa única em token inválido.

### Regenerar as fixtures com o SDK oficial

```bash
pip install tuya-connector-python==0.1.2 pycryptodome websocket-client requests
python3 tools/gen_fixtures.py > test/fixtures.json
```

As credenciais nas fixtures são **fictícias**.

## Uso

```ts
import { TuyaClient, PulsarConsumer, TUYA_API_ENDPOINTS, TUYA_PULSAR_ENDPOINTS } from './src/index.ts';

const tuya = new TuyaClient({
  endpoint: TUYA_API_ENDPOINTS.us,          // data center da conta do app (confirmar para o Brasil)
  clientId: process.env.TUYA_CLIENT_ID!,
  secret: process.env.TUYA_SECRET!,          // somente no servidor
});

await tuya.sendCommands(deviceId, [{ code: 'switch_led', value: true }]);

new PulsarConsumer({
  accessId: process.env.TUYA_CLIENT_ID!,
  secret: process.env.TUYA_SECRET!,
  wsEndpoint: TUYA_PULSAR_ENDPOINTS.us,
  onEvent: (evt) => console.log(evt),        // { devId, status: [{ code, value, t }] }
  onError: console.error,
}).start();
```

## O que **não** está provado

- **Nenhuma chamada real à Tuya foi feita** (não há credenciais). Os testes provam que este código gera o mesmo que o SDK oficial, não que uma conta/projeto específico será aceito.
- `POST /v1.0/iot-03/devices/{id}/commands` é o padrão documentado, mas **não o vi em código**: confirmar no primeiro teste real (spike S1).
- O código de erro `1010` (token inválido) usado no *retry* é uma **premissa** a validar.
- Mensagens com `encryptModel` **GCM** são **recusadas explicitamente**; implementar só depois de ver uma mensagem real.
- A verificação TLS do WebSocket está **ligada** (o SDK Python a desativa com `ssl.CERT_NONE`). Se o certificado do endpoint falhar, investigue-o; não desligue a verificação.
- O ACK é enviado **sempre**, mesmo se o handler falhar (o erro vai para `onError`), para evitar laço de reentrega; se precisar de entrega garantida, acrescente uma fila de *dead-letter*.
