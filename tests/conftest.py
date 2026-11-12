import copy
import json

import httpx
import pytest
import respx

from app.config import PAYPAL_SANDBOX_BASE_URL, load_settings
from app.db import connect, init_db
from app.paypal import PayPalClient

BASE = PAYPAL_SANDBOX_BASE_URL


def make_settings(tmp_path, **overrides):
    env = {
        "PAYPAL_ENV": "sandbox",
        "PAYPAL_CLIENT_ID": "test-client",
        "PAYPAL_CLIENT_SECRET": "test-secret",
        "APP_BASE_URL": "http://testserver",
        "AI_MODE": "replay",
        "DATABASE_PATH": str(tmp_path / "test.db"),
    }
    env.update(overrides)
    return load_settings(env)


class FakePayPal:
    """Minimal in-memory PayPal Orders v2 sandbox, served through respx."""

    def __init__(self, router: respx.Router):
        self.orders: dict[str, dict] = {}
        self.created_bodies: list[dict] = []
        self.capture_calls = 0
        self.request_ids: list[str] = []
        self.get_status_override: int | None = None
        self.approve_link_host = "www.sandbox.paypal.com"
        router.post(f"{BASE}/v1/oauth2/token").mock(
            return_value=httpx.Response(200, json={"access_token": "tok", "expires_in": 3600})
        )
        router.post(f"{BASE}/v2/checkout/orders").mock(side_effect=self._create)
        router.get(url__regex=rf"{BASE}/v2/checkout/orders/(?P<oid>[^/]+)$").mock(
            side_effect=self._get
        )
        router.post(url__regex=rf"{BASE}/v2/checkout/orders/(?P<oid>[^/]+)/capture$").mock(
            side_effect=self._capture
        )

    def _create(self, request):
        body = json.loads(request.content)
        self.created_bodies.append(body)
        self.request_ids.append(request.headers.get("PayPal-Request-Id"))
        oid = f"PP{len(self.orders) + 1}"
        self.orders[oid] = {"id": oid, "status": "PAYER_ACTION_REQUIRED",
                            "purchase_units": copy.deepcopy(body["purchase_units"])}
        return httpx.Response(201, json={
            "id": oid, "status": "PAYER_ACTION_REQUIRED",
            "links": [{"rel": "payer-action",
                       "href": f"https://{self.approve_link_host}/checkoutnow?token={oid}"}],
        })

    def _get(self, request, oid):
        if self.get_status_override:
            return httpx.Response(self.get_status_override, json={"name": "RESOURCE_NOT_FOUND"})
        if oid not in self.orders:
            return httpx.Response(404, json={"name": "RESOURCE_NOT_FOUND"})
        return httpx.Response(200, json=self.orders[oid])

    def _capture(self, request, oid):
        self.capture_calls += 1
        self.request_ids.append(request.headers.get("PayPal-Request-Id"))
        o = self.orders[oid]
        if o["status"] != "APPROVED":
            return httpx.Response(422, json={"name": "UNPROCESSABLE_ENTITY"})
        o["status"] = "COMPLETED"
        amount = o["purchase_units"][0]["amount"]
        return httpx.Response(201, json={
            "id": oid, "status": "COMPLETED",
            "purchase_units": [{"payments": {"captures": [{
                "id": f"CAP-{oid}", "status": "COMPLETED",
                "amount": {"currency_code": amount["currency_code"], "value": amount["value"]},
            }]}}],
        })

    # helpers for tests
    def approve(self, oid: str):
        self.orders[oid]["status"] = "APPROVED"


@pytest.fixture
def settings(tmp_path):
    return make_settings(tmp_path)


@pytest.fixture
def conn(settings):
    c = connect(settings.database_path)
    init_db(c)
    yield c
    c.close()


@pytest.fixture
def fake_paypal():
    with respx.mock(assert_all_called=False) as router:
        yield FakePayPal(router)


@pytest.fixture
def paypal(settings, fake_paypal):
    return PayPalClient(settings, http=httpx.Client(base_url=BASE))
