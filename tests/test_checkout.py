import sqlite3

import pytest

from app import checkout
from app.checkout import CheckoutError, NotApprovedError, capture_after_approval, create_checkout
from app.config import ConfigError, load_settings


def _buy(conn, paypal, items=None):
    items = items or [{"sku": "JKT-RAIN-01", "qty": 1}]
    return create_checkout(conn, paypal, "http://testserver", items, actor="test")


def _state(conn, order_id):
    return checkout.get_order(conn, order_id)["state"]


# ---- sandbox-only guard ----

@pytest.mark.parametrize("env_value", ["", "live", "production", "LIVE"])
def test_refuses_to_start_outside_sandbox(env_value):
    with pytest.raises(ConfigError):
        load_settings({"PAYPAL_ENV": env_value})


def test_paypal_client_pinned_to_sandbox(settings):
    from dataclasses import replace

    from app.paypal import PayPalClient
    with pytest.raises(RuntimeError):
        PayPalClient(replace(settings, paypal_base_url="https://api-m.paypal.com"))


def test_base_url_falls_back_to_render_url():
    s = load_settings({"PAYPAL_ENV": "sandbox", "RENDER_EXTERNAL_URL": "https://x.onrender.com/"})
    assert s.app_base_url == "https://x.onrender.com"
    s2 = load_settings({"PAYPAL_ENV": "sandbox", "APP_BASE_URL": "https://mine.example",
                        "RENDER_EXTERNAL_URL": "https://x.onrender.com"})
    assert s2.app_base_url == "https://mine.example"


# ---- server-side totals ----

def test_total_comes_from_catalog_not_client(conn, paypal, fake_paypal):
    co = _buy(conn, paypal, [{"sku": "JKT-RAIN-01", "qty": 2, "price": 0.01}])
    assert co["total"] == "148.00"
    sent = fake_paypal.created_bodies[0]["purchase_units"][0]
    assert sent["amount"]["value"] == "148.00"
    assert sent["items"][0]["unit_amount"]["value"] == "74.00"


@pytest.mark.parametrize("items", [
    [], [{"sku": "NOPE", "qty": 1}], [{"sku": "JKT-RAIN-01", "qty": 0}],
    [{"sku": "JKT-RAIN-01", "qty": 11}], [{"sku": "JKT-RAIN-01", "qty": "2"}],
    [{"sku": "JKT-DOWN-03", "qty": 4}],  # only 3 in stock
])
def test_bad_carts_rejected(conn, paypal, fake_paypal, items):
    with pytest.raises(CheckoutError):
        create_checkout(conn, paypal, "http://testserver", items, actor="test")
    assert fake_paypal.created_bodies == []


def test_create_uses_idempotency_key(conn, paypal, fake_paypal):
    co = _buy(conn, paypal)
    assert fake_paypal.request_ids[0] == f"create-{co['order_id']}"


def test_rejects_non_sandbox_approval_link(conn, paypal, fake_paypal):
    fake_paypal.approve_link_host = "evil.example.com"
    with pytest.raises(CheckoutError):
        _buy(conn, paypal)


# ---- capture rules ----

def test_happy_path_captures_once_after_approval(conn, paypal, fake_paypal):
    co = _buy(conn, paypal)
    fake_paypal.approve("PP1")
    order = capture_after_approval(conn, paypal, "PP1")
    assert order["state"] == "CAPTURED"
    assert order["capture_id"] == "CAP-PP1"
    assert fake_paypal.capture_calls == 1
    assert fake_paypal.request_ids[-1] == f"capture-{co['order_id']}"
    stock = conn.execute("SELECT stock FROM products WHERE sku='JKT-RAIN-01'").fetchone()[0]
    assert stock == 5


def test_capture_before_approval_is_blocked(conn, paypal, fake_paypal):
    co = _buy(conn, paypal)
    with pytest.raises(NotApprovedError):
        capture_after_approval(conn, paypal, "PP1")
    assert fake_paypal.capture_calls == 0
    assert _state(conn, co["order_id"]) == "AWAITING_APPROVAL"


def test_double_capture_is_blocked(conn, paypal, fake_paypal):
    _buy(conn, paypal)
    fake_paypal.approve("PP1")
    capture_after_approval(conn, paypal, "PP1")
    again = capture_after_approval(conn, paypal, "PP1")  # buyer refreshes the return page
    assert again["state"] == "CAPTURED"
    assert fake_paypal.capture_calls == 1


def test_capture_in_progress_is_not_repeated(conn, paypal, fake_paypal):
    co = _buy(conn, paypal)
    fake_paypal.approve("PP1")
    checkout.transition(conn, co["order_id"], "CAPTURING", "test")
    with pytest.raises(CheckoutError):
        capture_after_approval(conn, paypal, "PP1")
    assert fake_paypal.capture_calls == 0


def test_tampered_amount_is_not_captured(conn, paypal, fake_paypal):
    co = _buy(conn, paypal)
    fake_paypal.approve("PP1")
    fake_paypal.orders["PP1"]["purchase_units"][0]["amount"]["value"] = "1.00"
    with pytest.raises(CheckoutError):
        capture_after_approval(conn, paypal, "PP1")
    assert fake_paypal.capture_calls == 0
    assert _state(conn, co["order_id"]) == "FAILED"


def test_tampered_currency_is_not_captured(conn, paypal, fake_paypal):
    _buy(conn, paypal)
    fake_paypal.approve("PP1")
    fake_paypal.orders["PP1"]["purchase_units"][0]["amount"]["currency_code"] = "EUR"
    with pytest.raises(CheckoutError):
        capture_after_approval(conn, paypal, "PP1")
    assert fake_paypal.capture_calls == 0


def test_expired_order_is_failed_without_capture(conn, paypal, fake_paypal):
    co = _buy(conn, paypal)
    fake_paypal.get_status_override = 404
    with pytest.raises(NotApprovedError):
        capture_after_approval(conn, paypal, "PP1")
    assert fake_paypal.capture_calls == 0
    assert _state(conn, co["order_id"]) == "FAILED"


def test_unknown_paypal_order_rejected(conn, paypal, fake_paypal):
    with pytest.raises(CheckoutError):
        capture_after_approval(conn, paypal, "PP-UNKNOWN")


def test_cancelled_order_cannot_be_captured(conn, paypal, fake_paypal):
    co = _buy(conn, paypal)
    checkout.cancel_by_buyer(conn, "PP1")
    fake_paypal.approve("PP1")
    with pytest.raises(CheckoutError):
        capture_after_approval(conn, paypal, "PP1")
    assert fake_paypal.capture_calls == 0
    assert _state(conn, co["order_id"]) == "CANCELLED"


# ---- state machine and audit ----

def test_illegal_transition_rejected(conn, paypal, fake_paypal):
    co = _buy(conn, paypal)
    with pytest.raises(checkout.InvalidTransition):
        checkout.transition(conn, co["order_id"], "CAPTURED", "test")


def test_audit_log_records_every_step_and_is_append_only(conn, paypal, fake_paypal):
    co = _buy(conn, paypal)
    fake_paypal.approve("PP1")
    capture_after_approval(conn, paypal, "PP1")
    states = [a["to_state"] for a in checkout.audit_trail(conn, co["order_id"])]
    assert states == ["PENDING_PAYPAL", "AWAITING_APPROVAL", "CAPTURING", "CAPTURED"]
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute("UPDATE audit_log SET detail = 'x'")
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute("DELETE FROM audit_log")
