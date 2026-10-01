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
npm test            # 27 testes
npm run typecheck   # tsc --noEmit
```

Os testes provam:

- **Assinatura** idêntica à do SDK oficial em 5 casos (token, status, query desordenada, POST com corpo, IR).
- **Senha, URL e decriptação do Pulsar** idênticas às do SDK; formato de **duas camadas** e `protocol` conforme a doc oficial.
- **Consumidor**: valida cabeçalhos no handshake, entrega o evento, faz ACK e **reconecta** após queda (contra um servidor WebSocket simulado).
- **Cliente** (com `fetch` falso): token reutilizado, refresh perto da expiração, **o corpo enviado é o corpo assinado**, erro tipado, nova tentativa **única** nos erros de token **1010/1011/1012** (e nenhuma no 1106).

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
  endpoint: TUYA_API_ENDPOINTS.ueaz,        // Brasil: Eastern America (confirmar no vínculo; pode ser `us`)
  clientId: process.env.TUYA_CLIENT_ID!,
  secret: process.env.TUYA_SECRET!,          // somente no servidor
});

await tuya.sendCommands(deviceId, [{ code: 'switch_led', value: true }]);

new PulsarConsumer({
  accessId: process.env.TUYA_CLIENT_ID!,
  secret: process.env.TUYA_SECRET!,
  wsEndpoint: TUYA_PULSAR_ENDPOINTS.ueaz,
  onEvent: (evt, meta) => console.log(meta.protocol, evt),   // protocolo 4: { devId, status: [{ code, value, t }] }
  onError: console.error,
}).start();
```

## O que **não** está provado

- **Nenhuma chamada real à Tuya foi feita** (não há credenciais). Os testes provam que este código gera o mesmo que o SDK oficial, não que uma conta/projeto específico será aceito.
- **Rota de comandos:** `POST /v1.0/iot-03/devices/{id}/commands` não aparece em nenhuma fonte oficial que li; a tabela de limites cita `POST /v2.0/cloud/thing/{id}/shadow/properties/issue`. **Testar as duas no spike S1.**
- **Endpoint WebSocket do Eastern America** (`wss://mqe-ueaz.tuyaus.com:8285/`): a doc só lista o Pulsar nativo (7285); o 8285 é **inferido do padrão**.
- Erros de token (**1010** expirado, **1011** inválido, **1012** status inválido) vêm da página oficial *Global Error Codes*.
- **Criptografia:** AES/ECB é o padrão documentado; **AES/GCM** é opcional no console e **não está implementado** (`encryption: 'gcm'` lança erro).
- A **verificação do `sign` (MD5)** da mensagem é opcional na doc e **não está implementada**.
- **Limite de 4 comandos/s por projeto** (doc oficial): o cliente **não** impõe fila; isso é responsabilidade do *command bus* ([`docs/03`](../../docs/03-arquitetura-e-stack.md) §5.1).
- A verificação TLS do WebSocket está **ligada** (o SDK Python a desativa com `ssl.CERT_NONE`). Se o certificado do endpoint falhar, investigue-o; não desligue a verificação.
- O ACK é enviado **sempre**, mesmo se o handler falhar (o erro vai para `onError`), para evitar laço de reentrega; se precisar de entrega garantida, acrescente uma fila de *dead-letter*.
