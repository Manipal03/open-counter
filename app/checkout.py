"""Checkout service: the only code that moves money.

- Totals are computed here from the catalog. Prices from the AI or the browser are never used.
- Every order state change goes through `transition`, which also writes the audit log.
- Capture happens only after PayPal reports the order APPROVED and the amount, currency and
  cart hash match what we stored. A local CAPTURING lock plus PayPal-Request-Id prevent
  double capture.
"""

import hashlib
import json
import sqlite3
import uuid
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit

from app.catalog import format_money, get_product
from app.paypal import PayPalClient, PayPalError

MAX_LINES = 10
MAX_QTY = 10
SHOP_NAME = "Open Counter Demo Shop"

ALLOWED = {
    "PENDING_PAYPAL": {"AWAITING_APPROVAL", "FAILED"},
    "AWAITING_APPROVAL": {"CAPTURING", "CANCELLED", "FAILED"},
    "CAPTURING": {"CAPTURED", "FAILED", "AWAITING_APPROVAL"},
    "CAPTURED": set(),
    "FAILED": set(),
    "CANCELLED": set(),
}


class CheckoutError(Exception):
    """A problem the shopper can be told about."""


class NotApprovedError(CheckoutError):
    pass


class InvalidTransition(Exception):
    pass


# ---------- state machine ----------

def get_order(conn: sqlite3.Connection, order_id: str) -> dict | None:
    r = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    return dict(r) if r else None


def get_order_by_paypal_id(conn: sqlite3.Connection, paypal_order_id: str) -> dict | None:
    r = conn.execute(
        "SELECT * FROM orders WHERE paypal_order_id = ?", (paypal_order_id,)
    ).fetchone()
    return dict(r) if r else None


def _audit(conn, order_id, from_state, to_state, actor, detail):
    conn.execute(
        "INSERT INTO audit_log (order_id, from_state, to_state, actor, detail) VALUES (?,?,?,?,?)",
        (order_id, from_state, to_state, actor, detail),
    )


_UPDATABLE = {"paypal_order_id", "approve_url", "capture_id", "failure_reason"}


def transition(
    conn: sqlite3.Connection,
    order_id: str,
    to_state: str,
    actor: str,
    detail: str = "",
    expected_from: str | None = None,
    **fields,
) -> dict:
    """Move an order to `to_state` atomically. Raises InvalidTransition if not allowed."""
    bad = set(fields) - _UPDATABLE
    if bad:
        raise ValueError(f"cannot update fields: {bad}")
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute("SELECT state FROM orders WHERE id = ?", (order_id,)).fetchone()
        if row is None:
            raise InvalidTransition(f"order {order_id} not found")
        current = row["state"]
        if expected_from is not None and current != expected_from:
            raise InvalidTransition(f"expected {expected_from}, order is {current}")
        if to_state not in ALLOWED.get(current, set()):
            raise InvalidTransition(f"{current} -> {to_state} not allowed")
        cols = [f"{k} = ?" for k in fields] + ["state = ?", "updated_at = datetime('now')"]
        sets = ", ".join(cols)
        conn.execute(
            f"UPDATE orders SET {sets} WHERE id = ?", (*fields.values(), to_state, order_id)
        )
        _audit(conn, order_id, current, to_state, actor, detail)
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return get_order(conn, order_id)


def audit_trail(conn: sqlite3.Connection, order_id: str) -> list[dict]:
    rows = conn.execute("SELECT * FROM audit_log WHERE order_id = ? ORDER BY id", (order_id,))
    return [dict(r) for r in rows]


# ---------- cart ----------

def build_cart(conn: sqlite3.Connection, items: list[dict]) -> dict:
    """Validate SKUs/quantities and price the cart from the catalog. Ignores any price input."""
    if not isinstance(items, list) or not items:
        raise CheckoutError("The cart is empty.")
    merged: dict[str, int] = {}
    for item in items:
        if not isinstance(item, dict):
            raise CheckoutError("Each cart item needs a sku and a qty.")
        sku = str(item.get("sku", "")).strip()
        qty = item.get("qty")
        if not sku or isinstance(qty, bool) or not isinstance(qty, int):
            raise CheckoutError("Each cart item needs a sku and a whole-number qty.")
        merged[sku] = merged.get(sku, 0) + qty
    if len(merged) > MAX_LINES:
        raise CheckoutError(f"A cart can have at most {MAX_LINES} different products.")

    lines, currency, total = [], None, 0
    for sku, qty in merged.items():
        if qty < 1 or qty > MAX_QTY:
            raise CheckoutError(f"Quantity for {sku} must be between 1 and {MAX_QTY}.")
        product = get_product(conn, sku)
        if product is None:
            raise CheckoutError(f"Unknown product {sku}.")
        if product["stock"] < qty:
            raise CheckoutError(f"Only {product['stock']} of {product['name']} left.")
        if currency and product["currency"] != currency:
            raise CheckoutError("All items must use the same currency.")
        currency = product["currency"]
        line_total = product["price_cents"] * qty
        total += line_total
        lines.append(
            {
                "sku": sku,
                "name": product["name"],
                "qty": qty,
                "unit_cents": product["price_cents"],
                "line_cents": line_total,
            }
        )
    canonical = json.dumps(
        [[li["sku"], li["qty"], li["unit_cents"]] for li in lines] + [currency, total],
        separators=(",", ":"),
    )
    return {
        "lines": lines,
        "currency": currency,
        "total_cents": total,
        "cart_hash": hashlib.sha256(canonical.encode()).hexdigest()[:32],
    }


def _paypal_order_body(order_id: str, cart: dict, base_url: str) -> dict:
    cur = cart["currency"]
    return {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": order_id,
                "custom_id": cart["cart_hash"],
                "description": f"{SHOP_NAME} order",
                "amount": {
                    "currency_code": cur,
                    "value": format_money(cart["total_cents"], cur),
                    "breakdown": {
                        "item_total": {
                            "currency_code": cur,
                            "value": format_money(cart["total_cents"], cur),
                        }
                    },
                },
                "items": [
                    {
                        "name": li["name"][:127],
                        "sku": li["sku"],
                        "quantity": str(li["qty"]),
                        "unit_amount": {
                            "currency_code": cur,
                            "value": format_money(li["unit_cents"], cur),
                        },
                    }
                    for li in cart["lines"]
                ],
            }
        ],
        "payment_source": {
            "paypal": {
                "experience_context": {
                    "brand_name": SHOP_NAME,
                    "shipping_preference": "NO_SHIPPING",
                    "user_action": "PAY_NOW",
                    "return_url": f"{base_url}/checkout/return",
                    "cancel_url": f"{base_url}/checkout/cancel",
                }
            }
        },
    }


def create_checkout(
    conn: sqlite3.Connection, paypal: PayPalClient, base_url: str, items: list[dict], actor: str
) -> dict:
    cart = build_cart(conn, items)
    order_id = uuid.uuid4().hex
    conn.execute("BEGIN IMMEDIATE")
    conn.execute(
        "INSERT INTO orders (id, state, items_json, total_cents, currency, cart_hash)"
        " VALUES (?, 'PENDING_PAYPAL', ?, ?, ?, ?)",
        (order_id, json.dumps(cart["lines"]), cart["total_cents"], cart["currency"],
         cart["cart_hash"]),
    )
    _audit(conn, order_id, None, "PENDING_PAYPAL", actor,
           f"cart priced from catalog: {format_money(cart['total_cents'], cart['currency'])} "
           f"{cart['currency']}")
    conn.execute("COMMIT")

    try:
        pp = paypal.create_order(_paypal_order_body(order_id, cart, base_url), f"create-{order_id}")
    except PayPalError as exc:
        transition(conn, order_id, "FAILED", "system", f"PayPal create failed ({exc.status_code})",
                   failure_reason="Could not create the PayPal order.")
        raise CheckoutError("PayPal is not available right now. Please try again.") from exc

    approve_url = next(
        (lk["href"] for lk in pp.get("links", []) if lk.get("rel") in ("payer-action", "approve")),
        None,
    )
    if approve_url and urlsplit(approve_url).hostname != "www.sandbox.paypal.com":
        approve_url = None
    if not pp.get("id") or not approve_url:
        transition(conn, order_id, "FAILED", "system", "PayPal response had no approval link",
                   failure_reason="PayPal did not return an approval link.")
        raise CheckoutError("PayPal did not return an approval link.")

    transition(conn, order_id, "AWAITING_APPROVAL", "system", f"PayPal order {pp['id']} created",
               paypal_order_id=pp["id"], approve_url=approve_url)
    return {
        "order_id": order_id,
        "lines": cart["lines"],
        "total": format_money(cart["total_cents"], cart["currency"]),
        "currency": cart["currency"],
        "approve_url": approve_url,
    }


# ---------- return from PayPal ----------

def _to_cents(value: object) -> int | None:
    try:
        d = Decimal(str(value))
    except (InvalidOperation, TypeError):
        return None
    if d != d.quantize(Decimal("0.01")):
        return None
    return int(d * 100)


def _amount_matches(amount: dict | None, order: dict) -> bool:
    if not isinstance(amount, dict):
        return False
    return (
        amount.get("currency_code") == order["currency"]
        and _to_cents(amount.get("value")) == order["total_cents"]
    )


def _fail(conn, order, detail, reason):
    return transition(conn, order["id"], "FAILED", "system", detail, failure_reason=reason)


def capture_after_approval(
    conn: sqlite3.Connection, paypal: PayPalClient, paypal_order_id: str
) -> dict:
    """Called when the buyer returns from PayPal. Captures at most once."""
    order = get_order_by_paypal_id(conn, paypal_order_id)
    if order is None:
        raise CheckoutError("We don't recognise that order.")
    if order["state"] == "CAPTURED":
        return order
    if order["state"] != "AWAITING_APPROVAL":
        raise CheckoutError(f"This order can't be paid (status: {order['state']}).")

    try:
        pp = paypal.get_order(paypal_order_id)
    except PayPalError as exc:
        if exc.status_code == 404:
            _fail(conn, order, "PayPal order not found or expired",
                  "The PayPal order expired. Please start a new checkout.")
            raise NotApprovedError("This PayPal order has expired. Please start again.") from exc
        raise CheckoutError("Could not reach PayPal. Please refresh to try again.") from exc

    if pp.get("status") != "APPROVED":
        raise NotApprovedError("The payment hasn't been approved in PayPal yet.")

    units = pp.get("purchase_units") or [{}]
    unit = units[0]
    if len(units) != 1 or not _amount_matches(unit.get("amount"), order) or \
            unit.get("custom_id") != order["cart_hash"]:
        _fail(conn, order, "PayPal amount/currency/cart did not match stored cart",
              "The payment amount didn't match the cart, so nothing was charged.")
        raise CheckoutError("The payment amount didn't match the cart, so nothing was charged.")

    try:
        transition(conn, order["id"], "CAPTURING", "system", "buyer approved in PayPal",
                   expected_from="AWAITING_APPROVAL")
    except InvalidTransition:
        latest = get_order(conn, order["id"])
        if latest["state"] == "CAPTURED":
            return latest
        raise CheckoutError("This payment is already being processed.") from None

    try:
        cap = paypal.capture_order(paypal_order_id, f"capture-{order['id']}")
    except PayPalError as exc:
        if exc.retryable:
            transition(conn, order["id"], "AWAITING_APPROVAL", "system",
                       f"capture call failed ({exc.status_code}); can retry")
            raise CheckoutError("PayPal didn't respond. Please refresh to try again.") from exc
        _fail(conn, order, f"capture rejected ({exc.status_code})", "PayPal declined the capture.")
        raise CheckoutError("PayPal declined the payment.") from exc

    try:
        capture = cap["purchase_units"][0]["payments"]["captures"][0]
    except (KeyError, IndexError, TypeError):
        capture = {}
    if cap.get("status") != "COMPLETED" or capture.get("status") != "COMPLETED" or \
            not _amount_matches(capture.get("amount"), order):
        _fail(conn, order, f"capture not completed: {cap.get('status')}/{capture.get('status')}",
              "The payment didn't complete.")
        raise CheckoutError("The payment didn't complete.")

    conn.execute("BEGIN IMMEDIATE")
    for li in json.loads(order["items_json"]):
        conn.execute("UPDATE products SET stock = MAX(stock - ?, 0) WHERE sku = ?",
                     (li["qty"], li["sku"]))
    conn.execute("COMMIT")
    return transition(conn, order["id"], "CAPTURED", "system",
                      f"captured {capture.get('id')}", capture_id=capture.get("id"))


def cancel_by_buyer(conn: sqlite3.Connection, paypal_order_id: str) -> dict | None:
    order = get_order_by_paypal_id(conn, paypal_order_id)
    if order and order["state"] == "AWAITING_APPROVAL":
        return transition(conn, order["id"], "CANCELLED", "buyer", "buyer cancelled at PayPal")
    return order
