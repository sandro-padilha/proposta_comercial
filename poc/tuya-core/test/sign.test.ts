import assert from 'node:assert/strict';
import { test } from 'node:test';
import { canonicalUrl, sha256Hex, sign, stringToSign } from '../src/sign.ts';
import type { SignParts } from '../src/sign.ts';
import fixtures from './fixtures.json' with { type: 'json' };

for (const c of fixtures.sign) {
  test(`assinatura idêntica à do SDK Python oficial: ${c.name}`, () => {
    const input = c.input as unknown as SignParts;
    assert.equal(sign({ ...input, accessToken: input.accessToken ?? undefined }), c.expected);
  });
}

test('SHA-256 de corpo vazio é a constante conhecida', () => {
  assert.equal(sha256Hex(''), 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855');
});

test('query é ordenada por chave', () => {
  assert.equal(
    canonicalUrl('/v1.0/x', { page_size: 20, last_id: 'x1', category: 'dj' }),
    '/v1.0/x?category=dj&last_id=x1&page_size=20',
  );
});

test('stringToSign tem a forma MÉTODO\\nHASH\\n\\nURL', () => {
  const s = stringToSign({ method: 'get', path: '/v1.0/token', query: { grant_type: 1 } });
  assert.equal(s, `GET\n${sha256Hex('')}\n\n/v1.0/token?grant_type=1`);
});

test('o hash do corpo depende dos bytes exatos enviados', () => {
  const a = sign({ clientId: 'c', secret: 's', t: 1, method: 'POST', path: '/p', bodyRaw: '{"a":1}' });
  const b = sign({ clientId: 'c', secret: 's', t: 1, method: 'POST', path: '/p', bodyRaw: '{"a": 1}' });
  assert.notEqual(a, b);
});
