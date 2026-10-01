import assert from 'node:assert/strict';
import { once } from 'node:events';
import type { AddressInfo } from 'node:net';
import { test } from 'node:test';
import { WebSocketServer } from 'ws';
import {
  PulsarConsumer,
  TUYA_PULSAR_ENDPOINTS,
  UnsupportedEncryptionError,
  decodeFrame,
  decryptData,
  pulsarPassword,
  pulsarUrl,
} from '../src/pulsar.ts';
import fixtures from './fixtures.json' with { type: 'json' };

const p = fixtures.pulsar;

test('senha do handshake idêntica à do SDK Python oficial', () => {
  assert.equal(pulsarPassword(p.accessId, p.secret), p.expectedPassword);
});

test('URL do consumidor idêntica à do SDK Python oficial', () => {
  assert.equal(pulsarUrl(p.wsEndpoint, p.accessId), p.expectedUrl);
});

test('decriptação AES-128-ECB compatível com o SDK', () => {
  assert.deepEqual(JSON.parse(decryptData(p.data, p.secret)), p.event);
});

test('decodeFrame extrai messageId, protocolo (1ª camada) e evento (2ª camada)', () => {
  const m = decodeFrame(p.frameRaw, p.secret);
  assert.equal(m.messageId, 'CAEQ-teste-1');
  assert.equal(m.protocol, 4);
  assert.equal(m.pv, '2.0');
  assert.equal(typeof m.t, 'number');
  assert.deepEqual(m.event, p.event);
});

test('modo GCM (opcional no console) é recusado explicitamente, sem decifrar errado em silêncio', () => {
  assert.throws(() => decodeFrame(p.frameRaw, p.secret, 'gcm'), UnsupportedEncryptionError);
});

test('endpoints: Eastern America (Brasil, apps novos) está disponível', () => {
  assert.equal(TUYA_PULSAR_ENDPOINTS.ueaz, 'wss://mqe-ueaz.tuyaus.com:8285/');
});

test('consumidor: valida credenciais no handshake, entrega o evento e faz ACK', async () => {
  const seenHeaders: Array<Record<string, string | string[] | undefined>> = [];
  const acks: string[] = [];
  const wss = new WebSocketServer({
    port: 0,
    verifyClient: ({ req }, done) => {
      seenHeaders.push(req.headers);
      done(req.headers.username === p.accessId && req.headers.password === p.expectedPassword, 401);
    },
  });
  await once(wss, 'listening');
  wss.on('connection', (ws) => {
    ws.on('message', (m) => acks.push((JSON.parse(m.toString()) as { messageId: string }).messageId));
    ws.send(p.frameRaw);
  });

  const events: unknown[] = [];
  const metas: Array<{ messageId: string; protocol: number }> = [];
  const got = Promise.withResolvers<void>();
  const consumer = new PulsarConsumer({
    accessId: p.accessId,
    secret: p.secret,
    wsEndpoint: `ws://127.0.0.1:${(wss.address() as AddressInfo).port}/`,
    onEvent: (e, meta) => {
      events.push(e);
      metas.push(meta);
      got.resolve();
    },
    onError: got.reject,
  });
  consumer.start();
  try {
    await got.promise;
    await new Promise((r) => setTimeout(r, 100)); // dá tempo ao ACK chegar
    assert.deepEqual(events, [p.event]);
    assert.equal(metas[0]?.protocol, 4, 'o protocolo chega ao handler para classificar a mensagem');
    assert.deepEqual(acks, ['CAEQ-teste-1']);
    assert.equal(seenHeaders[0]?.username, p.accessId);
  } finally {
    consumer.stop();
    wss.close();
  }
});

test('consumidor: reconecta sozinho depois de uma queda', async () => {
  let connections = 0;
  const wss = new WebSocketServer({ port: 0 });
  await once(wss, 'listening');
  wss.on('connection', (ws) => {
    connections += 1;
    if (connections === 1) ws.close(); // derruba a primeira conexão
    else ws.send(p.frameRaw);
  });

  const got = Promise.withResolvers<void>();
  const consumer = new PulsarConsumer({
    accessId: p.accessId,
    secret: p.secret,
    wsEndpoint: `ws://127.0.0.1:${(wss.address() as AddressInfo).port}/`,
    reconnectMinMs: 20,
    reconnectMaxMs: 50,
    onEvent: () => got.resolve(),
  });
  consumer.start();
  try {
    await got.promise;
    assert.ok(connections >= 2);
  } finally {
    consumer.stop();
    wss.close();
  }
});
