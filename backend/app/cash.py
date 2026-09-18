from __future__ import annotations

from app import db
from app.orders import _load_order, _venue, close_order, deliver_order, order_out
METHODS = ("cash", "card", "transfer", "other")


def _shift_out(shift: dict, payments: list[dict] | None = None) -> dict:
    pays = payments if payments is not None else _payments(shift["id"])
    by_method = {m: 0 for m in METHODS}
    tips = 0
    cash_tips = 0
    for p in pays:
        by_method[p["method"]] = by_method.get(p["method"], 0) + p["amount_cents"]
        tip = p.get("tip_cents") or 0
        tips += tip
        if p["method"] == "cash":
            cash_tips += tip
    refunds = db.fetch_all(
        "SELECT method, amount_cents, tip_cents FROM refunds WHERE shift_id = %s",
        (shift["id"],),
    ) if shift.get("id") else []
    refund_total = 0
    cash_refunds = 0
    for r in refunds:
        refund_total += (r["amount_cents"] or 0) + (r.get("tip_cents") or 0)
        if r["method"] == "cash":
            cash_refunds += (r["amount_cents"] or 0) + (r.get("tip_cents") or 0)
    expected_cash = (shift.get("opening_cash_cents") or 0) + by_method["cash"] + cash_tips - cash_refunds
    counted = shift.get("counted_cash_cents")
    return {
        "id": shift["id"],
        "status": shift["status"],
        "opening_cash_cents": shift["opening_cash_cents"],
        "counted_cash_cents": counted,
        "opened_at": shift["opened_at"].isoformat() if shift.get("opened_at") else None,
        "closed_at": shift["closed_at"].isoformat() if shift.get("closed_at") else None,
        "totals": {
            "by_method": by_method,
            "tips_cents": tips,
            "refund_cents": refund_total,
            "sales_cents": sum(by_method.values()),
            "expected_cash_cents": expected_cash,
            "difference_cents": None if counted is None else counted - expected_cash,
        },
        "payments": [
            {
                "id": p["id"],
                "order_id": p["order_id"],
                "method": p["method"],
                "amount_cents": p["amount_cents"],
                "tip_cents": p.get("tip_cents") or 0,
            }
            for p in pays
        ],
    }


def _payments(shift_id: int) -> list[dict]:
    return db.fetch_all(
        "SELECT * FROM payments WHERE shift_id = %s ORDER BY id",
        (shift_id,),
    )


def day_report() -> dict:
    venue = _venue()
    tz = venue.get("timezone") or "UTC"
    rows = db.fetch_all(
        """
        SELECT id FROM orders
        WHERE venue_id = %s
          AND status = 'closed'
          AND closed_at IS NOT NULL
          AND (closed_at AT TIME ZONE %s)::date = (now() AT TIME ZONE %s)::date
        ORDER BY closed_at
        """,
        (venue["id"], tz, tz),
    )
    receipts = []
    gross = discount = tax = tips = collected = refunded_sum = 0
    for row in rows:
        bundle = _load_order(row["id"])
        if not bundle:
            continue
        body = order_out(bundle)
        pays = db.fetch_all(
            """
            SELECT method, amount_cents, tip_cents
            FROM payments WHERE order_id = %s ORDER BY id
            """,
            (row["id"],),
        )
        methods = []
        rec_tips = 0
        rec_paid = 0
        for p in pays:
            rec_paid += p["amount_cents"] or 0
            rec_tips += p.get("tip_cents") or 0
            if p["method"] not in methods:
                methods.append(p["method"])
        ref = db.fetch_one(
            """
            SELECT COALESCE(SUM(amount_cents + tip_cents), 0) AS n
            FROM refunds WHERE order_id = %s
            """,
            (row["id"],),
        )
        rec_refund = int(ref["n"]) if ref else 0
        pc = body["precuenta"]
        gross += pc.get("subtotal_cents") or 0
        discount += pc.get("discount_cents") or 0
        tax += pc.get("tax_cents") or 0
        tips += rec_tips
        collected += rec_paid
        refunded_sum += rec_refund
        space = body.get("space")
        receipts.append(
            {
                "id": body["id"],
                "closed_at": bundle["order"]["closed_at"].isoformat()
                if bundle["order"].get("closed_at")
                else None,
                "space": {"key": space["key"], "name": space["name"]} if space else None,
                "subtotal_cents": pc.get("subtotal_cents") or 0,
                "discount_cents": pc.get("discount_cents") or 0,
                "tax_cents": pc.get("tax_cents") or 0,
                "total_cents": pc.get("total_cents") or 0,
                "collected_cents": rec_paid,
                "tips_cents": rec_tips,
                "refund_cents": rec_refund,
                "refunded": bool(bundle["order"].get("refunded_at")) or rec_refund > 0,
                "methods": methods,
            }
        )
    day = db.fetch_one("SELECT (now() AT TIME ZONE %s)::date AS d", (tz,))
    return {
        "date": str(day["d"]) if day else None,
        "tax_enabled": bool(venue.get("tax_enabled")),
        "tax_bps": int(venue.get("tax_bps") or 0),
        "gross_cents": gross,
        "discount_cents": discount,
        "tax_cents": tax,
        "tips_cents": tips,
        "collected_cents": collected,
        "refund_cents": refunded_sum,
        "receipt_count": len(receipts),
        "receipts": receipts,
    }


def current_shift() -> dict | None:
    venue = _venue()
    row = db.fetch_one(
        """
        SELECT * FROM cash_shifts
        WHERE venue_id = %s AND status = 'open'
        ORDER BY id DESC LIMIT 1
        """,
        (venue["id"],),
    )
    if not row:
        return None
    return _shift_out(row)


def open_shift(opening_cash_cents: int = 0) -> dict:
    venue = _venue()
    existing = db.fetch_one(
        "SELECT id FROM cash_shifts WHERE venue_id = %s AND status = 'open'",
        (venue["id"],),
    )
    if existing:
        raise ValueError("Ya hay un turno abierto")
    row = db.fetch_one(
        """
        INSERT INTO cash_shifts (venue_id, status, opening_cash_cents)
        VALUES (%s, 'open', %s)
        RETURNING *
        """,
        (venue["id"], max(0, opening_cash_cents)),
    )
    return _shift_out(row, [])


def close_shift(counted_cash_cents: int) -> dict:
    shift = db.fetch_one(
        """
        SELECT * FROM cash_shifts
        WHERE venue_id = %s AND status = 'open'
        ORDER BY id DESC LIMIT 1
        """,
        (_venue()["id"],),
    )
    if not shift:
        raise ValueError("No hay turno abierto")
    db.execute(
        """
        UPDATE cash_shifts
        SET status = 'closed', counted_cash_cents = %s, closed_at = now()
        WHERE id = %s
        """,
        (counted_cash_cents, shift["id"]),
    )
    row = db.fetch_one("SELECT * FROM cash_shifts WHERE id = %s", (shift["id"],))
    return _shift_out(row)


def order_balance(order_id: int) -> dict:
    bundle = _load_order(order_id)
    if not bundle:
        raise ValueError("Orden no encontrada")
    body = order_out(bundle)
    paid = db.fetch_one(
        """
        SELECT COALESCE(SUM(amount_cents), 0) AS paid,
               COALESCE(SUM(tip_cents), 0) AS tips
        FROM payments WHERE order_id = %s
        """,
        (order_id,),
    )
    due = body["due_cents"]
    return {
        "order": body,
        "paid_cents": paid["paid"],
        "tips_cents": paid["tips"],
        "due_cents": due,
    }


def pay_order(order_id: int, method: str, amount_cents: int, tip_cents: int = 0) -> dict:
    method = (method or "").strip().lower()
    if method not in METHODS:
        raise ValueError("Medio de pago no válido")
    if amount_cents <= 0:
        raise ValueError("El monto debe ser mayor a cero")

    shift = db.fetch_one(
        """
        SELECT * FROM cash_shifts
        WHERE venue_id = %s AND status = 'open'
        ORDER BY id DESC LIMIT 1
        """,
        (_venue()["id"],),
    )
    if not shift:
        raise ValueError("Abre un turno de caja antes de cobrar")

    bal = order_balance(order_id)
    if bal["order"]["status"] in {"closed", "void"}:
        raise ValueError("La orden ya está cerrada")
    if amount_cents > bal["due_cents"]:
        raise ValueError("El monto supera lo que falta por pagar")

    db.fetch_one(
        """
        INSERT INTO payments (shift_id, order_id, method, amount_cents, tip_cents)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (shift["id"], order_id, method, amount_cents, max(0, tip_cents)),
    )
    bal = order_balance(order_id)
    if bal["due_cents"] == 0:
        if bal["order"]["status"] not in {"delivered", "closed"}:
            try:
                deliver_order(order_id)
            except ValueError:
                pass
        try:
            close_order(order_id)
        except ValueError:
            pass
        bal = order_balance(order_id)
    bal["shift"] = current_shift()
    return bal


def refund_order(order_id: int) -> dict:
    bundle = _load_order(order_id)
    if not bundle:
        raise ValueError("Orden no encontrada")
    order = bundle["order"]
    if order["status"] != "closed":
        raise ValueError("Solo se reembolsa un recibo cerrado")
    if order.get("refunded_at"):
        raise ValueError("El recibo ya fue reembolsado")

    pays = db.fetch_all(
        "SELECT method, amount_cents, tip_cents FROM payments WHERE order_id = %s ORDER BY id",
        (order_id,),
    )
    if not pays:
        raise ValueError("No hay cobro que devolver")

    shift = db.fetch_one(
        """
        SELECT * FROM cash_shifts
        WHERE venue_id = %s AND status = 'open'
        ORDER BY id DESC LIMIT 1
        """,
        (_venue()["id"],),
    )
    if not shift:
        raise ValueError("Abre un turno de caja antes de reembolsar")

    methods = []
    amount = 0
    tips = 0
    for p in pays:
        amount += p["amount_cents"] or 0
        tips += p.get("tip_cents") or 0
        if p["method"] not in methods:
            methods.append(p["method"])
    method = methods[0] if len(methods) == 1 else "refund"

    db.fetch_one(
        """
        INSERT INTO refunds (shift_id, order_id, method, amount_cents, tip_cents)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (shift["id"], order_id, method, amount, tips),
    )
    db.execute("UPDATE orders SET refunded_at = now() WHERE id = %s", (order_id,))
    return {
        "ok": True,
        "order_id": order_id,
        "method": method,
        "amount_cents": amount,
        "tip_cents": tips,
        "refund_cents": amount + tips,
        "report": day_report(),
    }
