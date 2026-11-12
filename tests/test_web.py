from fastapi.testclient import TestClient

from app.main import create_app


def test_end_to_end_replay_purchase(settings, paypal, fake_paypal):
    app = create_app(settings=settings, paypal=paypal)
    client = TestClient(app)

    assert client.get("/health").json()["paypal_env"] == "sandbox"
    page = client.get("/")
    assert page.status_code == 200
    assert "scripted replies" in page.text

    r1 = client.post("/api/chat", json={"message": "waterproof jacket under $80"}).json()
    assert "Stormline" in r1["text"]
    r2 = client.post("/api/chat", json={"message": "buy the first one"}).json()
    assert r2["checkout"]["total"] == "74.00"
    assert r2["checkout"]["approve_url"].startswith("https://www.sandbox.paypal.com/")

    # Returning before approval must not capture.
    early = client.get("/checkout/return", params={"token": "PP1"})
    assert "Payment not completed" in early.text
    assert fake_paypal.capture_calls == 0

    fake_paypal.approve("PP1")
    done = client.get("/checkout/return", params={"token": "PP1", "PayerID": "X"})
    assert "Payment complete" in done.text
    assert fake_paypal.capture_calls == 1

    orders = client.get("/orders")
    assert "CAPTURED" in orders.text


def test_cancel_page(settings, paypal, fake_paypal):
    client = TestClient(create_app(settings=settings, paypal=paypal))
    client.post("/api/chat", json={"message": "beanie"})
    client.post("/api/chat", json={"message": "buy it"})
    r = client.get("/checkout/cancel", params={"token": "PP1"})
    assert "Nothing was charged" in r.text
