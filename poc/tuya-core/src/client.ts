import { sign } from './sign.ts';
import type { QueryValue } from './sign.ts';

/**
 * Endpoints regionais da Open API.
 *
 * - `us` = Western America (Oregon) · `ueaz` = Eastern America (Virginia) · `eu` = Central Europe ·
 *   `weaz` = Western Europe · `in` · `cn` · `sg`.
 * - Nomes dos data centers: doc oficial "Data Center". `ueaz`/`weaz` vêm dos nomes originais
 *   ("America Azure" / "Europe MS") enumerados no SDK oficial.
 * - **Brasil:** apps registrados desde 2025-11-25 caem no **Eastern America** (`ueaz`); apps anteriores
 *   ficam no Western America (`us`). Para o app Smart Life a regra exata não está documentada: confirme no
 *   primeiro vínculo (o data center do projeto precisa casar com o da conta).
 */
export const TUYA_API_ENDPOINTS = {
  us: 'https://openapi.tuyaus.com',
  ueaz: 'https://openapi-ueaz.tuyaus.com',
  eu: 'https://openapi.tuyaeu.com',
  weaz: 'https://openapi-weaz.tuyaeu.com',
  in: 'https://openapi.tuyain.com',
  cn: 'https://openapi.tuyacn.com',
  sg: 'https://openapi-sg.iotbing.com',
} as const;

/** Códigos de erro relevantes (página oficial "Global Error Codes"). */
export const TUYA_ERROR = {
  SIGN_INVALID: 1004,
  TOKEN_EXPIRED: 1010,
  TOKEN_INVALID: 1011,
  TOKEN_STATUS_INVALID: 1012,
  PERMISSION_DENIED: 1106,
  CONCURRENT_LIMIT: 1110,
  TOO_FREQUENT: 1199,
  DEVICE_OFFLINE: 2001,
  IP_CROSS_REGION: 2007,
  COMMAND_NOT_SUPPORTED: 2008,
  NO_PLAN: 28841001,
  PLAN_EXPIRED: 28841002,
  PLAN_BILL_OVERDUE: 28841003,
  TRIAL_QUOTA_EXHAUSTED: 28841004,
  API_NOT_SUBSCRIBED: 28841101,
  API_QUOTA_EXHAUSTED: 28841104,
  PROJECT_NOT_AUTHORIZED: 28841105,
} as const;

/** Erros de token: renovar o token e repetir a chamada uma única vez. */
const TOKEN_ERROR_CODES = new Set<number>([
  TUYA_ERROR.TOKEN_EXPIRED,
  TUYA_ERROR.TOKEN_INVALID,
  TUYA_ERROR.TOKEN_STATUS_INVALID,
]);

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
      if (!(err instanceof TuyaApiError) || !TOKEN_ERROR_CODES.has(Number(err.code))) throw err;
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
