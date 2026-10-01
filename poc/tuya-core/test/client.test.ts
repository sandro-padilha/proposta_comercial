import assert from 'node:assert/strict';
import { test } from 'node:test';
import { TuyaApiError, TuyaClient } from '../src/client.ts';
import { sign } from '../src/sign.ts';

interface Call {
  url: string;
  method: string;
  headers: Record<string, string>;
  body?: string;
}

function fakeFetch(handler: (c: Call) => unknown): { fetch: typeof fetch; calls: Call[] } {
  const calls: Call[] = [];
  const f = (async (url: string, init: RequestInit) => {
    const call: Call = {
      url,
      method: init.method ?? 'GET',
      headers: init.headers as Record<string, string>,
      body: init.body as string | undefined,
    };
    calls.push(call);
    return { status: 200, json: async () => handler(call) } as Response;
  }) as unknown as typeof fetch;
  return { fetch: f, calls };
}

const ok = (result: unknown) => ({ success: true, t: 1, result });
const tokenResult = (n: number) => ok({ access_token: `at${n}`, refresh_token: `rt${n}`, expire_time: 7200 });

function make(handler: (c: Call) => unknown, now: { v: number }) {
  const { fetch, calls } = fakeFetch(handler);
  const client = new TuyaClient({
    endpoint: 'https://openapi.tuyaus.com',
    clientId: 'cid',
    secret: 'sec',
    fetch,
    now: () => now.v,
  });
  return { client, calls };
}

test('pede token (grant_type=1), assina e reutiliza o token', async () => {
  const now = { v: 1_751_000_000_000 };
  const { client, calls } = make((c) => (c.url.includes('/v1.0/token') ? tokenResult(1) : ok([{ code: 'switch_led', value: true }])), now);

  const status = await client.getStatus('dev1');
  await client.getStatus('dev1');

  assert.deepEqual(status, [{ code: 'switch_led', value: true }]);
  assert.equal(calls.filter((c) => c.url.includes('/v1.0/token')).length, 1, 'apenas um pedido de token');
  assert.equal(calls[0]?.url, 'https://openapi.tuyaus.com/v1.0/token?grant_type=1');
  assert.equal(calls[0]?.headers.access_token, '');

  const call = calls[1]!;
  assert.equal(call.headers.access_token, 'at1');
  assert.equal(call.headers.sign_method, 'HMAC-SHA256');
  assert.equal(
    call.headers.sign,
    sign({ clientId: 'cid', secret: 'sec', accessToken: 'at1', t: call.headers.t!, method: 'GET', path: '/v1.0/iot-03/devices/dev1/status' }),
  );
});

test('comando: o corpo enviado é exatamente o corpo assinado', async () => {
  const now = { v: 1_751_000_000_000 };
  const { client, calls } = make((c) => (c.url.includes('/v1.0/token') ? tokenResult(1) : ok(true)), now);

  await client.sendCommands('dev1', [{ code: 'switch_led', value: false }]);

  const call = calls[1]!;
  assert.equal(call.method, 'POST');
  assert.equal(call.body, '{"commands":[{"code":"switch_led","value":false}]}');
  assert.equal(call.headers['content-type'], 'application/json');
  assert.equal(
    call.headers.sign,
    sign({ clientId: 'cid', secret: 'sec', accessToken: 'at1', t: call.headers.t!, method: 'POST', path: '/v1.0/iot-03/devices/dev1/commands', bodyRaw: call.body }),
  );
});

test('renova o token pelo refresh_token quando está perto de expirar', async () => {
  const now = { v: 1_751_000_000_000 };
  let n = 0;
  const { client, calls } = make((c) => (c.url.includes('/v1.0/token') ? tokenResult(++n) : ok([])), now);

  await client.getStatus('dev1');
  now.v += 7200 * 1000 - 30_000; // faltam 30 s: dentro da margem de 60 s
  await client.getStatus('dev1');

  const refresh = calls.find((c) => c.url.includes('/v1.0/token/rt1'));
  assert.ok(refresh, 'usou o refresh_token do primeiro token');
  assert.equal(calls.at(-1)?.headers.access_token, 'at2');
});

test('erro da API vira TuyaApiError com código', async () => {
  const now = { v: 1_751_000_000_000 };
  const { client } = make(
    (c) => (c.url.includes('/v1.0/token') ? tokenResult(1) : { success: false, code: 2001, msg: 'permission deny', tid: 't-1' }),
    now,
  );
  await assert.rejects(client.getStatus('dev1'), (e: unknown) => e instanceof TuyaApiError && e.code === 2001 && e.tid === 't-1');
});

test('token inválido (1010): renova e tenta uma única vez', async () => {
  const now = { v: 1_751_000_000_000 };
  let n = 0;
  let businessCalls = 0;
  const { client } = make((c) => {
    if (c.url.includes('/v1.0/token')) return tokenResult(++n);
    return ++businessCalls === 1 ? { success: false, code: 1010, msg: 'token invalid' } : ok(['ok']);
  }, now);
  assert.deepEqual(await client.getStatus('dev1'), ['ok']);
  assert.equal(businessCalls, 2);
});

test('rota de ar-condicionado por IR usa o caminho e o corpo esperados', async () => {
  const now = { v: 1_751_000_000_000 };
  const { client, calls } = make((c) => (c.url.includes('/v1.0/token') ? tokenResult(1) : ok(true)), now);
  await client.acScene('ir1', 'ac1', { power: 1, mode: 1, temp: 24, wind: 1 });
  const call = calls[1]!;
  assert.equal(call.url, 'https://openapi.tuyaus.com/v2.0/infrareds/ir1/air-conditioners/ac1/scenes/command');
  assert.equal(call.body, '{"power":1,"mode":1,"temp":24,"wind":1}');
});
