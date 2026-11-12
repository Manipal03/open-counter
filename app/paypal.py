"""Thin PayPal Orders v2 REST client, pinned to the sandbox host.

Endpoints used (PayPal docs, verified):
- POST /v1/oauth2/token                      client-credentials access token
- POST /v2/checkout/orders                   create order
- GET  /v2/checkout/orders/{id}              show order details
- POST /v2/checkout/orders/{id}/capture      capture payment for an approved order
https://developer.paypal.com/docs/api/orders/v2/
"""

import time

import httpx

from app.config import PAYPAL_SANDBOX_BASE_URL, Settings


class PayPalError(Exception):
    def __init__(self, status_code: int, body: object):
        super().__init__(f"PayPal API error {status_code}")
        self.status_code = status_code
        self.body = body

    @property
    def retryable(self) -> bool:
        return self.status_code == 0 or self.status_code >= 500


class PayPalClient:
    def __init__(self, settings: Settings, http: httpx.Client | None = None):
        if settings.paypal_base_url != PAYPAL_SANDBOX_BASE_URL:
            raise RuntimeError("PayPal base URL must be the sandbox host.")
        self._settings = settings
        self._http = http or httpx.Client(base_url=PAYPAL_SANDBOX_BASE_URL, timeout=20.0)
        self._token: str | None = None
        self._token_expires_at = 0.0

    @property
    def configured(self) -> bool:
        return bool(self._settings.paypal_client_id and self._settings.paypal_client_secret)

    def _access_token(self) -> str:
        if self._token and time.monotonic() < self._token_expires_at:
            return self._token
        resp = self._send(
            "POST",
            "/v1/oauth2/token",
            auth=(self._settings.paypal_client_id, self._settings.paypal_client_secret),
            data={"grant_type": "client_credentials"},
        )
        self._token = resp["access_token"]
        self._token_expires_at = time.monotonic() + max(0, int(resp.get("expires_in", 0)) - 60)
        return self._token

    def _send(self, method: str, path: str, **kwargs) -> dict:
        try:
            r = self._http.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise PayPalError(0, str(exc)) from exc
        try:
            body = r.json() if r.content else {}
        except ValueError:
            body = r.text
        if r.status_code >= 400:
            raise PayPalError(r.status_code, body)
        return body

    def _authed(self, method: str, path: str, request_id: str | None = None, **kwargs) -> dict:
        headers = {"Authorization": f"Bearer {self._access_token()}"}
        if request_id:
            headers["PayPal-Request-Id"] = request_id
        if method == "POST":
            headers["Content-Type"] = "application/json"
        return self._send(method, path, headers=headers, **kwargs)

    def create_order(self, body: dict, request_id: str) -> dict:
        return self._authed("POST", "/v2/checkout/orders", request_id=request_id, json=body)

    def get_order(self, paypal_order_id: str) -> dict:
        return self._authed("GET", f"/v2/checkout/orders/{paypal_order_id}")

    def capture_order(self, paypal_order_id: str, request_id: str) -> dict:
        return self._authed(
            "POST", f"/v2/checkout/orders/{paypal_order_id}/capture", request_id=request_id, json={}
        )
