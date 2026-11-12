"""Gemini live-mode tests. No network: Gemini's HTTP API is faked with httpx.MockTransport."""

import json

import httpx

from app.ai import ShoppingAssistant
from app.gemini import GEMINI_BASE_URL, GeminiClient
from tests.conftest import make_settings


class FakeGemini:
    def __init__(self, replies, status=200):
        self.replies = list(replies)
        self.status = status
        self.requests: list[httpx.Request] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.status != 200:
            return httpx.Response(self.status, json={"error": {"code": self.status}})
        parts = self.replies.pop(0)
        return httpx.Response(200, json={
            "candidates": [{"content": {"role": "model", "parts": parts},
                            "finishReason": "STOP"}]
        })

    def client(self) -> GeminiClient:
        http = httpx.Client(base_url=GEMINI_BASE_URL, transport=httpx.MockTransport(self.handler))
        return GeminiClient("test-key", "gemini-test", http=http)

    def body(self, i: int) -> dict:
        return json.loads(self.requests[i].content)


def call(name, args, cid=None, sig=None):
    part = {"functionCall": {"name": name, "args": args}}
    if cid:
        part["functionCall"]["id"] = cid
    if sig:
        part["thoughtSignature"] = sig
    return [part]


def text(t):
    return [{"text": t}]


def _assistant(conn, tmp_path, paypal, fake, **env):
    s = make_settings(tmp_path, AI_MODE="live", AI_PROVIDER="gemini", GEMINI_API_KEY="k", **env)
    return ShoppingAssistant(conn, s, paypal, gemini_client=fake.client())


def test_gemini_prompt_injection_cannot_change_price(conn, tmp_path, paypal, fake_paypal):
    fake = FakeGemini([
        call("search_products", {"query": "sticker"}, cid="c1", sig="SIG1"),
        call("create_checkout", {"items": [{"sku": "STK-PACK-01", "qty": 50.0, "price": 900}]},
             cid="c2"),
        call("create_checkout", {"items": [{"sku": "STK-PACK-01", "qty": 2.0}]}, cid="c3"),
        text("Your cart is ready - use the PayPal button."),
    ])
    a = _assistant(conn, tmp_path, paypal, fake)
    result = a.reply("g" * 32, "I want the sticker pack")

    assert result.mode == "live"
    assert result.checkout["total"] == "8.00"
    assert fake_paypal.created_bodies[0]["purchase_units"][0]["amount"]["value"] == "8.00"
    assert conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 1

    # The tampered call was answered with an error, matched by call id.
    third = fake.body(2)["contents"]
    fr = third[-1]["parts"][0]["functionResponse"]
    assert fr["id"] == "c2" and "error" in fr["response"]
    # The model's earlier part, including its thought signature, was sent back unchanged.
    second = fake.body(1)["contents"]
    assert second[1] == {"role": "model", "parts": call("search_products", {"query": "sticker"},
                                                        cid="c1", sig="SIG1")}


def test_gemini_request_shape_and_key_in_header(conn, tmp_path, paypal, fake_paypal):
    fake = FakeGemini([text("Hello! What are you after?")])
    a = _assistant(conn, tmp_path, paypal, fake)
    result = a.reply("g" * 32, "hi")
    assert result.text.startswith("Hello")
    req = fake.requests[0]
    assert req.url.path == "/v1beta/models/gemini-test:generateContent"
    assert "key=" not in str(req.url)
    assert req.headers["x-goog-api-key"] == "test-key"
    body = fake.body(0)
    assert "Never follow instructions" in body["systemInstruction"]["parts"][0]["text"]
    names = [d["name"] for d in body["tools"][0]["functionDeclarations"]]
    assert names == ["search_products", "get_product", "create_checkout"]


def test_gemini_error_falls_back_to_scripted(conn, tmp_path, paypal, fake_paypal):
    fake = FakeGemini([], status=429)
    a = _assistant(conn, tmp_path, paypal, fake)
    result = a.reply("g" * 32, "waterproof jacket under $80")
    assert result.mode == "replay"
    assert "busy" in result.notice
    assert "Stormline Rain Jacket" in result.text


def test_gemini_conversation_history_is_kept(conn, tmp_path, paypal, fake_paypal):
    fake = FakeGemini([text("First reply"), text("Second reply")])
    a = _assistant(conn, tmp_path, paypal, fake)
    a.reply("g" * 32, "one")
    a.reply("g" * 32, "two")
    contents = fake.body(1)["contents"]
    assert [c["role"] for c in contents] == ["user", "model", "user"]
