import { createHash, createHmac } from 'node:crypto';

export type QueryValue = string | number | boolean;

export interface SignParts {
  clientId: string;
  secret: string;
  /** Vazio/ausente no pedido de token. */
  accessToken?: string;
  /** Epoch em milissegundos — o mesmo valor enviado no header `t`. */
  t: number | string;
  method: string;
  /** Caminho sem query string, ex.: `/v1.0/iot-03/devices/abc/status`. */
  path: string;
  query?: Record<string, QueryValue>;
  /** Corpo exatamente como será enviado: o hash é calculado sobre estes caracteres. */
  bodyRaw?: string;
}

export const sha256Hex = (s: string): string => createHash('sha256').update(s, 'utf8').digest('hex');

/** Query ordenada por chave e sem URL-encode, como no SDK oficial. */
export function canonicalUrl(path: string, query?: Record<string, QueryValue>): string {
  const keys = query ? Object.keys(query).sort() : [];
  if (keys.length === 0) return path;
  return `${path}?${keys.map((k) => `${k}=${query![k]}`).join('&')}`;
}

/** MÉTODO \n SHA256(corpo) \n (headers assinados — vazio) \n URL */
export function stringToSign(p: Pick<SignParts, 'method' | 'path' | 'query' | 'bodyRaw'>): string {
  return [p.method.toUpperCase(), sha256Hex(p.bodyRaw ?? ''), '', canonicalUrl(p.path, p.query)].join('\n');
}

/** HMAC-SHA256(secret, clientId + accessToken + t + stringToSign), em hexadecimal maiúsculo. */
export function sign(p: SignParts): string {
  const message = `${p.clientId}${p.accessToken ?? ''}${p.t}${stringToSign(p)}`;
  return createHmac('sha256', p.secret).update(message, 'utf8').digest('hex').toUpperCase();
}
