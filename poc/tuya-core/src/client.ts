import { sign } from './sign.ts';
import type { QueryValue } from './sign.ts';

/** Endpoints regionais (fonte: integração open-source tuya-smart-ir-ac e SDK oficial). */
export const TUYA_API_ENDPOINTS = {
  us: 'https://openapi.tuyaus.com',
  eu: 'https://openapi.tuyaeu.com',
  in: 'https://openapi.tuyain.com',
  cn: 'https://openapi.tuyacn.com',
  sg: 'https://openapi-sg.iotbing.com',
} as const;

export interface TuyaClientOptions {
  endpoint: string;
  clientId: string;
  secret: string;
  /** Injetável para teste. */
  fetch?: typeof fetch;
  now?: () => number;
  lang?: string;
}

interface Envelope<T> {
  success: boolean;
  t?: number;
  tid?: string;
  code?: number | string;
  msg?: string;
  result?: T;
}

interface TokenResult {
  access_token: string;
  refresh_token: string;
  /** Validade em segundos. */
  expire_time: number;
  uid?: string;
}

interface TokenInfo {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
}

export class TuyaApiError extends Error {
  readonly code: number | string | undefined;
  readonly tid: string | undefined;
  constructor(message: string, code?: number | string, tid?: string) {
    super(message);
    this.name = 'TuyaApiError';
    this.code = code;
    this.tid = tid;
  }
}

export interface DeviceCommand {
  code: string;
  value: unknown;
}

export interface AcState {
  power: 0 | 1;
  mode: number;
  temp: number;
  wind: number;
}

const TOKEN_SKEW_MS = 60_000;
/** Código de "token inválido" — premissa a validar no primeiro teste real. */
const TOKEN_INVALID_CODE = 1010;

export class TuyaClient {
  readonly #o: Required<Omit<TuyaClientOptions, 'fetch' | 'now'>> & { fetch: typeof fetch; now: () => number };
  #token: TokenInfo | undefined;
  #inflight: Promise<TokenInfo> | undefined;

  constructor(o: TuyaClientOptions) {
    this.#o = {
      lang: 'en',
      fetch: (...args) => fetch(...args),
      now: () => Date.now(),
      ...o,
    };
  }

  async request<T>(
    method: string,
    path: string,
    opts: { query?: Record<string, QueryValue>; body?: unknown } = {},
  ): Promise<T> {
    let token = await this.#getToken();
    try {
      return await this.#send<T>(method, path, opts, token.accessToken);
    } catch (err) {
      if (!(err instanceof TuyaApiError) || Number(err.code) !== TOKEN_INVALID_CODE) throw err;
      this.#token = undefined; // força novo token e tenta uma única vez
      token = await this.#getToken();
      return this.#send<T>(method, path, opts, token.accessToken);
    }
  }

  // --- Dispositivos (rotas do SDK Node oficial: /v1.0/iot-03/devices/...) ---

  getStatus(deviceId: string) {
    return this.request<Array<{ code: string; value: unknown }>>('GET', `/v1.0/iot-03/devices/${deviceId}/status`);
  }

  getSpecification(deviceId: string) {
    return this.request<unknown>('GET', `/v1.0/iot-03/devices/${deviceId}/specification`);
  }

  /** Rota POST de comandos: "provável" — confirmar no primeiro teste real. */
  sendCommands(deviceId: string, commands: DeviceCommand[]) {
    return this.request<boolean>('POST', `/v1.0/iot-03/devices/${deviceId}/commands`, { body: { commands } });
  }

  // --- Infravermelho (rotas confirmadas em integração open-source) ---

  acScene(infraredId: string, remoteId: string, state: AcState) {
    return this.request<boolean>(
      'POST',
      `/v2.0/infrareds/${infraredId}/air-conditioners/${remoteId}/scenes/command`,
      { body: state },
    );
  }

  irKeys(infraredId: string, remoteId: string) {
    return this.request<unknown>('GET', `/v2.0/infrareds/${infraredId}/remotes/${remoteId}/keys`);
  }

  irKey(infraredId: string, remoteId: string, key: { category_id: number | string; key_id: number | string; key: string }) {
    return this.request<boolean>('POST', `/v2.0/infrareds/${infraredId}/remotes/${remoteId}/raw/command`, { body: key });
  }

  // --- internos ---

  async #getToken(): Promise<TokenInfo> {
    const now = this.#o.now();
    if (this.#token && this.#token.expiresAt - TOKEN_SKEW_MS > now) return this.#token;
    this.#inflight ??= this.#renewToken().finally(() => {
      this.#inflight = undefined;
    });
    return this.#inflight;
  }

  async #renewToken(): Promise<TokenInfo> {
    const previous = this.#token;
    if (previous) {
      try {
        return await this.#storeToken(await this.#send<TokenResult>('GET', `/v1.0/token/${previous.refreshToken}`, {}));
      } catch {
        // refresh falhou: cai para um token novo
      }
    }
    return this.#storeToken(await this.#send<TokenResult>('GET', '/v1.0/token', { query: { grant_type: 1 } }));
  }

  #storeToken(r: TokenResult): TokenInfo {
    this.#token = {
      accessToken: r.access_token,
      refreshToken: r.refresh_token,
      expiresAt: this.#o.now() + r.expire_time * 1000,
    };
    return this.#token;
  }

  async #send<T>(
    method: string,
    path: string,
    opts: { query?: Record<string, QueryValue>; body?: unknown },
    accessToken?: string,
  ): Promise<T> {
    const t = this.#o.now();
    const bodyRaw = opts.body === undefined ? undefined : JSON.stringify(opts.body);
    const signature = sign({
      clientId: this.#o.clientId,
      secret: this.#o.secret,
      accessToken,
      t,
      method,
      path,
      query: opts.query,
      bodyRaw,
    });
    const qs = opts.query
      ? `?${Object.keys(opts.query)
          .sort()
          .map((k) => `${k}=${opts.query![k]}`)
          .join('&')}`
      : '';
    const res = await this.#o.fetch(`${this.#o.endpoint}${path}${qs}`, {
      method,
      body: bodyRaw,
      headers: {
        client_id: this.#o.clientId,
        sign: signature,
        sign_method: 'HMAC-SHA256',
        t: String(t),
        access_token: accessToken ?? '',
        lang: this.#o.lang,
        ...(bodyRaw === undefined ? {} : { 'content-type': 'application/json' }),
      },
    });
    const env = (await res.json()) as Envelope<T>;
    if (!env.success) throw new TuyaApiError(env.msg ?? `HTTP ${res.status}`, env.code, env.tid);
    return env.result as T;
  }
}
