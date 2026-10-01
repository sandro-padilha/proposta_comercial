import assert from 'node:assert/strict';
import { once } from 'node:events';
import type { AddressInfo } from 'node:net';
import { test } from 'node:test';
import { WebSocketServer } from 'ws';
import { PulsarConsumer, UnsupportedEncryptionError, decodeFrame, decryptData, pulsarPassword, pulsarUrl } from '../src/pulsar.ts';
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

test('decodeFrame extrai messageId e evento', () => {
  const { messageId, event } = decodeFrame(p.frameRaw, p.secret);
  assert.equal(messageId, 'CAEQ-teste-1');
  assert.deepEqual(event, p.event);
});

test('modelo GCM é recusado explicitamente (não decifra errado em silêncio)', () => {
  const inner = Buffer.from(JSON.stringify({ data: 'AAAA', encryptModel: 'aes_gcm' })).toString('base64');
  const raw = JSON.stringify({ messageId: 'm1', payload: inner });
  assert.throws(() => decodeFrame(raw, p.secret), UnsupportedEncryptionError);
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
  const got = Promise.withResolvers<void>();
  const consumer = new PulsarConsumer({
    accessId: p.accessId,
    secret: p.secret,
    wsEndpoint: `ws://127.0.0.1:${(wss.address() as AddressInfo).port}/`,
    onEvent: (e) => {
      events.push(e);
      got.resolve();
    },
    onError: got.reject,
  });
  consumer.start();
  try {
    await got.promise;
    await new Promise((r) => setTimeout(r, 100)); // dá tempo ao ACK chegar
    assert.deepEqual(events, [p.event]);
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
