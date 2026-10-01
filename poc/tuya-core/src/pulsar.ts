import { createDecipheriv, createHash } from 'node:crypto';
import WebSocket from 'ws';

/**
 * Endpoints WebSocket do Message Service (porta 8285).
 *
 * `us`, `eu`, `in`, `cn`, `sg` estão na página oficial do SDK Node. Para **Eastern America (`ueaz`)** e
 * **Western Europe (`weaz`)** a doc oficial só lista o endpoint Pulsar nativo (`pulsar+ssl://…:7285`); a
 * URL WebSocket (8285) abaixo é **inferida do mesmo padrão** e precisa de confirmação no primeiro teste.
 */
export const TUYA_PULSAR_ENDPOINTS = {
  us: 'wss://mqe.tuyaus.com:8285/',
  ueaz: 'wss://mqe-ueaz.tuyaus.com:8285/',
  eu: 'wss://mqe.tuyaeu.com:8285/',
  weaz: 'wss://mqe-weaz.tuyaeu.com:8285/',
  in: 'wss://mqe.tuyain.com:8285/',
  cn: 'wss://mqe.tuyacn.com:8285/',
  sg: 'wss://mqe-sg.iotbing.com:8285/',
} as const;

/** Modo de criptografia do Message Service. ECB é o padrão ao assinar o serviço; GCM só se ativado no console. */
export type PulsarEncryption = 'ecb' | 'gcm';

const md5Hex = (s: string): string => createHash('md5').update(s, 'utf8').digest('hex');

/** Senha do handshake: md5(accessId + md5(secret))[8:24]. */
export function pulsarPassword(accessId: string, secret: string): string {
  return md5Hex(accessId + md5Hex(secret)).slice(8, 24);
}

export function pulsarUrl(wsEndpoint: string, accessId: string, topic = 'event'): string {
  const base = wsEndpoint.endsWith('/') ? wsEndpoint : `${wsEndpoint}/`;
  return `${base}ws/v2/consumer/persistent/${accessId}/out/${topic}/${accessId}-sub?ackTimeoutMillis=3000&subscriptionType=Failover`;
}

export class UnsupportedEncryptionError extends Error {
  constructor(mode: string) {
    super(`Modo de criptografia não implementado: ${mode} (apenas AES/ECB, o padrão documentado, foi implementado)`);
    this.name = 'UnsupportedEncryptionError';
  }
}

/** AES-128-ECB com chave secret[8:24] e padding PKCS7, como no SDK oficial. */
export function decryptData(dataB64: string, secret: string): string {
  const key = Buffer.from(secret.slice(8, 24), 'utf8');
  const decipher = createDecipheriv('aes-128-ecb', key, null);
  return Buffer.concat([decipher.update(Buffer.from(dataB64, 'base64')), decipher.final()]).toString('utf8');
}

export interface PulsarFrame {
  messageId: string;
  payload: string;
}

export interface DecodedMessage {
  messageId: string;
  /**
   * Número do protocolo (1ª camada). Define o tipo de mensagem: `4` = status de dispositivo (legado),
   * `20` = online/offline (legado), `1000` = dados do dispositivo (IoT Core), `1001` = gestão de dispositivo.
   * Configurar os dois conjuntos de protocolo pode duplicar mensagens.
   */
  protocol: number;
  pv: string;
  /** Carimbo de tempo da 1ª camada. */
  t: number;
  /** 2ª camada, já decifrada (ex.: `{ devId, status: [{ code, value, t }] }` no protocolo 4). */
  event: unknown;
}

/**
 * Decodifica um quadro recebido. Formato oficial em duas camadas: `payload` (base64) → JSON com
 * `{ data, protocol, pv, t, sign }` → `data` cifrado (chave = 16 caracteres do meio do Access Secret).
 */
export function decodeFrame(raw: string, secret: string, encryption: PulsarEncryption = 'ecb'): DecodedMessage {
  if (encryption !== 'ecb') throw new UnsupportedEncryptionError(encryption);
  const frame = JSON.parse(raw) as PulsarFrame;
  const inner = JSON.parse(Buffer.from(frame.payload, 'base64').toString('utf8')) as {
    data: string;
    protocol: number;
    pv: string;
    t: number;
  };
  return {
    messageId: frame.messageId,
    protocol: inner.protocol,
    pv: inner.pv,
    t: inner.t,
    event: JSON.parse(decryptData(inner.data, secret)),
  };
}

export interface PulsarConsumerOptions {
  accessId: string;
  secret: string;
  wsEndpoint: string;
  /** `event` (produção, padrão) ou `event-test` (canal de teste: exige escolher os dispositivos de teste no console). */
  topic?: string;
  /** Deve coincidir com a configuração do console. Padrão `ecb`. */
  encryption?: PulsarEncryption;
  onEvent: (event: unknown, meta: Omit<DecodedMessage, 'event'>) => void | Promise<void>;
  onError?: (err: unknown) => void;
  reconnectMinMs?: number;
  reconnectMaxMs?: number;
  pingMs?: number;
  pongTimeoutMs?: number;
}

/**
 * Consumidor do Message Service da Tuya (Pulsar sobre WebSocket).
 * - A verificação TLS fica LIGADA (o SDK Python a desativa; não copie isso).
 * - Faz ACK sempre, mesmo se o handler falhar (erro vai para `onError`), para não criar laço de reentrega.
 */
export class PulsarConsumer {
  readonly #o: Required<PulsarConsumerOptions>;
  #ws: WebSocket | undefined;
  #stopped = true;
  #attempt = 0;
  #reconnectTimer: NodeJS.Timeout | undefined;
  #pingTimer: NodeJS.Timeout | undefined;
  #pongTimer: NodeJS.Timeout | undefined;

  constructor(o: PulsarConsumerOptions) {
    this.#o = {
      topic: 'event',
      encryption: 'ecb',
      onError: () => {},
      reconnectMinMs: 1_000,
      reconnectMaxMs: 30_000,
      pingMs: 30_000,
      pongTimeoutMs: 5_000,
      ...o,
    };
  }

  start(): void {
    if (!this.#stopped) return;
    this.#stopped = false;
    this.#connect();
  }

  stop(): void {
    this.#stopped = true;
    clearTimeout(this.#reconnectTimer);
    this.#clearPing();
    this.#ws?.terminate();
    this.#ws = undefined;
  }

  #connect(): void {
    const { accessId, secret, wsEndpoint, topic } = this.#o;
    const ws = new WebSocket(pulsarUrl(wsEndpoint, accessId, topic), {
      headers: { username: accessId, password: pulsarPassword(accessId, secret) },
    });
    this.#ws = ws;

    ws.on('open', () => {
      this.#attempt = 0;
      this.#pingTimer = setInterval(() => {
        ws.ping();
        this.#pongTimer = setTimeout(() => ws.terminate(), this.#o.pongTimeoutMs);
      }, this.#o.pingMs);
    });
    ws.on('pong', () => clearTimeout(this.#pongTimer));
    ws.on('message', (data) => {
      void this.#handle(ws, data.toString());
    });
    ws.on('error', (err) => this.#o.onError(err));
    ws.on('close', () => {
      this.#clearPing();
      if (this.#stopped) return;
      const base = Math.min(this.#o.reconnectMaxMs, this.#o.reconnectMinMs * 2 ** this.#attempt++);
      this.#reconnectTimer = setTimeout(() => this.#connect(), base * (0.5 + Math.random() / 2));
    });
  }

  async #handle(ws: WebSocket, raw: string): Promise<void> {
    let messageId: string | undefined;
    try {
      messageId = (JSON.parse(raw) as PulsarFrame).messageId;
      const { event, ...meta } = decodeFrame(raw, this.#o.secret, this.#o.encryption);
      await this.#o.onEvent(event, meta);
    } catch (err) {
      this.#o.onError(err);
    } finally {
      if (messageId && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ messageId }));
    }
  }

  #clearPing(): void {
    clearInterval(this.#pingTimer);
    clearTimeout(this.#pongTimer);
  }
}
