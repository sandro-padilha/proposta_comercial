#!/usr/bin/env python3
"""Gera test/fixtures.json usando o SDK Python OFICIAL da Tuya como referência.

Objetivo: provar que a assinatura e a decriptação em TypeScript produzem exatamente os
mesmos bytes que o SDK da Tuya (tuya-connector-python 0.1.2). Credenciais são fictícias.

Uso:
    pip install tuya-connector-python==0.1.2 pycryptodome websocket-client requests
    python3 tools/gen_fixtures.py > test/fixtures.json
"""
import base64
import json
import time
import types

from Crypto.Cipher import AES
from tuya_connector.openapi import TuyaOpenAPI
from tuya_connector.openpulsar import TuyaOpenPulsar

CLIENT_ID = "abcdefghij0123456789"
SECRET = "0123456789abcdef0123456789abcdef"
# Múltiplo de 1000: evita erro de ponto flutuante em int(time.time() * 1000) dentro do SDK.
T = 1751000000000


def sdk_sign(method, path, params=None, body=None, token=None):
    api = TuyaOpenAPI("https://openapi.tuyaus.com", CLIENT_ID, SECRET)
    if token:
        api.token_info = types.SimpleNamespace(access_token=token)
    real_time = time.time
    time.time = lambda: T / 1000
    try:
        sign, t = api._calculate_sign(method, path, params, body)
    finally:
        time.time = real_time
    assert t == T, (t, T)
    return sign


def case(name, method, path, params=None, body=None, token=None):
    return {
        "name": name,
        "input": {
            "clientId": CLIENT_ID,
            "secret": SECRET,
            "accessToken": token,
            "t": T,
            "method": method,
            "path": path,
            "query": params,
            # O SDK assina json.dumps(body) (separadores padrão do Python, com espaços) e envia o mesmo texto.
            "bodyRaw": json.dumps(body) if body else None,
        },
        "expected": sdk_sign(method, path, params, body, token),
    }


def pkcs7(b: bytes) -> bytes:
    n = 16 - len(b) % 16
    return b + bytes([n]) * n


def pulsar_fixture():
    access_id = "testid1234"
    endpoint = "wss://mqe.tuyaus.com:8285/"
    consumer = TuyaOpenPulsar(access_id, SECRET, endpoint, "event")
    password = consumer._TuyaOpenPulsar__gen_pwd()
    url = consumer._TuyaOpenPulsar__get_topic_url()

    event = {"devId": "bf0123456789abcdef", "status": [{"code": "switch_led", "value": True, "t": T}]}
    plaintext = json.dumps(event, separators=(",", ":"))
    key = SECRET[8:24].encode()
    data = base64.b64encode(AES.new(key, AES.MODE_ECB).encrypt(pkcs7(plaintext.encode()))).decode()
    # O próprio SDK deve conseguir decifrar o que geramos (prova que o formato é o do SDK).
    assert TuyaOpenPulsar._TuyaOpenPulsar__decrypt_by_aes(data, SECRET) == plaintext

    inner = {"data": data, "protocol": 4, "pv": "2.0", "sign": "ignorado", "t": T // 1000}
    payload = base64.b64encode(json.dumps(inner).encode()).decode()
    frame = {"messageId": "CAEQ-teste-1", "payload": payload, "properties": {}}
    return {
        "accessId": access_id,
        "secret": SECRET,
        "wsEndpoint": endpoint,
        "expectedPassword": password,
        "expectedUrl": url,
        "event": event,
        "data": data,
        "frameRaw": json.dumps(frame),
    }


def main():
    fixtures = {
        "note": "Gerado por tools/gen_fixtures.py com tuya-connector-python 0.1.2 (credenciais fictícias).",
        "sign": [
            case("token", "GET", "/v1.0/token", {"grant_type": 1}),
            case("status", "GET", "/v1.0/iot-03/devices/bf0123456789abcdef/status", token="tok_abc123"),
            case(
                "query-desordenada",
                "GET",
                "/v1.0/iot-03/devices",
                {"page_size": 20, "last_id": "x1", "category": "dj"},
                token="tok_abc123",
            ),
            case(
                "post-comandos",
                "POST",
                "/v1.0/iot-03/devices/bf0123456789abcdef/commands",
                body={"commands": [{"code": "switch_led", "value": True}]},
                token="tok_abc123",
            ),
            case(
                "post-ar-condicionado",
                "POST",
                "/v2.0/infrareds/bf01/air-conditioners/bf02/scenes/command",
                body={"power": 1, "mode": 1, "temp": 24, "wind": 1},
                token="tok_abc123",
            ),
        ],
        "pulsar": pulsar_fixture(),
    }
    print(json.dumps(fixtures, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
