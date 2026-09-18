from __future__ import annotations

from app import db
from app.mechanisms import mechanism_for
from app.profiles import PROFILES, resolve_modules
from app.settings import settings

ACTIVE = ("open", "sent", "in_progress", "ready", "delivered")
FLOOR_KINDS = {"table", "tab"}

ORIGIN_BY_SPACE = {
    "table": "sala",
    "tab": "barra",
    "counter": "mostrador",
    "queue": "mostrador",
    "line": "mostrador",
    "kiosk": "kiosko",
}

DINING_OPTIONS = ("dine_in", "takeout", "delivery")
DINING_LABELS = {
    "dine_in": "Comer aquí",
    "takeout": "Para llevar",
    "delivery": "Delivery",
}


def _dining(option: str | None) -> str:
    opt = (option or "").strip().lower()
    if opt not in DINING_OPTIONS:
        raise ValueError("Tipo de pedido no válido")
    return opt


def _profile() -> str:
    p = settings.hermes_profile.strip().lower()
    return p if p in PROFILES else "restaurant"


def _venue() -> dict:
    row = db.fetch_one("SELECT * FROM venues WHERE slug = %s", (settings.venue_slug,))
    if not row:
        raise RuntimeError("No hay venue demo")
    return row


def _load_order(order_id: int) -> dict | None:
    order = db.fetch_one("SELECT * FROM orders WHERE id = %s", (order_id,))
    if not order:
        return None
    items = db.fetch_all(
        """
        SELECT i.*, s.key AS station_key, s.name AS station_name
        FROM order_items i
        LEFT JOIN stations s ON s.id = i.station_id
        WHERE i.order_id = %s
        ORDER BY i.id
        """,
        (order_id,),
    )
    space = None
    if order.get("space_id"):
        space = db.fetch_one("SELECT * FROM spaces WHERE id = %s", (order["space_id"],))
    return {"order": order, "items": items, "space": space}


def _item_mods(item_id: int) -> list[dict]:
    try:
        rows = db.fetch_all(
            "SELECT name, price_delta_cents FROM order_item_modifiers WHERE item_id = %s ORDER BY id",
            (item_id,),
        )
    except Exception:
        return []
    return [{"name": r["name"], "price_delta_cents": r["price_delta_cents"]} for r in rows]


def order_out(bundle: dict) -> dict:
    order = bundle["order"]
    items = bundle["items"]
    space = bundle.get("space")
    subtotal = sum((i.get("price_cents") or 0) * i["qty"] for i in items if i["status"] != "void")
    paid_row = db.fetch_one(
        "SELECT COALESCE(SUM(amount_cents), 0) AS paid FROM payments WHERE order_id = %s",
        (order["id"],),
    )
    paid = paid_row["paid"] if paid_row else 0
    kind = order.get("discount_type") or None
    raw = int(order.get("discount_value") or 0)
    if kind == "percent" and raw > 0:
        discount = min(subtotal, subtotal * raw // 100)
    elif kind == "amount" and raw > 0:
        discount = min(subtotal, raw)
        kind = "amount"
    else:
        discount = 0
        kind = None
        raw = 0
    net = max(0, subtotal - discount)
    tax_on = bool(order.get("tax_enabled"))
    bps = max(0, min(10000, int(order.get("tax_bps") or 0)))
    tax = net * bps // 10000 if tax_on and bps else 0
    total = net + tax
    return {
        "id": order["id"],
        "status": order["status"],
        "origin": order["origin"],
        "dining_option": order.get("dining_option"),
        "dining_label": DINING_LABELS.get(order.get("dining_option") or ""),
        "cover_count": order.get("cover_count"),
        "queue_number": order.get("queue_number"),
        "notes": order.get("notes"),
        "opened_at": order["opened_at"].isoformat() if order.get("opened_at") else None,
        "space": (
            {"id": space["id"], "key": space["key"], "name": space["name"], "kind": space["kind"]}
            if space
            else None
        ),
        "items": [
            {
                "id": i["id"],
                "name": i["name_snapshot"],
                "qty": i["qty"],
                "price_cents": i.get("price_cents") or 0,
                "status": i["status"],
                "notes": i.get("notes"),
                "station": i.get("station_key"),
                "station_name": i.get("station_name"),
                "sent_at": i["sent_at"].isoformat() if i.get("sent_at") else None,
                "modifiers": _item_mods(i["id"]),
            }
            for i in items
        ],
        "discount": {"type": kind, "value": raw} if kind else None,
        "tax_enabled": tax_on,
        "tax_bps": bps if tax_on else 0,
        "precuenta": {
            "item_count": sum(i["qty"] for i in items if i["status"] != "void"),
            "subtotal_cents": subtotal,
            "discount_cents": discount,
            "tax_cents": tax,
            "total_cents": total,
        },
        "paid_cents": paid,
        "due_cents": max(0, total - paid),
        "refunded": bool(order.get("refunded_at")),
        "refunded_at": order["refunded_at"].isoformat() if order.get("refunded_at") else None,
    }


def cds_ticket() -> dict:
    venue = _venue()
    row = db.fetch_one(
        """
        SELECT o.id
        FROM orders o
        WHERE o.venue_id = %s AND o.status = ANY(%s)
        ORDER BY (
            SELECT COALESCE(MAX(i.id), 0) FROM order_items i WHERE i.order_id = o.id
        ) DESC, o.id DESC
        LIMIT 1
        """,
        (venue["id"], list(ACTIVE)),
    )
    if not row:
        return {"ticket": None}
    bundle = _load_order(row["id"])
    if not bundle:
        return {"ticket": None}
    body = order_out(bundle)
    body["items"] = [i for i in body["items"] if i["status"] != "void"]
    return {"ticket": body}


def list_open() -> list[dict]:
    venue = _venue()
    rows = db.fetch_all(
        """
        SELECT id FROM orders
        WHERE venue_id = %s AND status = ANY(%s)
        ORDER BY opened_at
        """,
        (venue["id"], list(ACTIVE)),
    )
    out = []
    for row in rows:
        bundle = _load_order(row["id"])
        if bundle:
            out.append(order_out(bundle))
    return out


def open_order(space_id: int, cover_count: int | None = None, dining_option: str | None = None) -> dict:
    venue = _venue()
    mech = mechanism_for(_profile())
    space = db.fetch_one(
        "SELECT * FROM spaces WHERE id = %s AND venue_id = %s",
        (space_id, venue["id"]),
    )
    if not space:
        raise ValueError("Espacio no encontrado")

    shared = space["kind"] in {"kiosk", "queue", "counter"}
    if not shared:
        existing = db.fetch_one(
            """
            SELECT id FROM orders
            WHERE venue_id = %s AND space_id = %s AND status = ANY(%s)
            """,
            (venue["id"], space_id, list(ACTIVE)),
        )
        if existing:
            bundle = _load_order(existing["id"])
            assert bundle
            if not _has_payments(existing["id"]):
                if dining_option:
                    db.execute(
                        "UPDATE orders SET dining_option = %s WHERE id = %s",
                        (_dining(dining_option), existing["id"]),
                    )
                if bundle["order"].get("tax_enabled") is None:
                    db.execute(
                        "UPDATE orders SET tax_enabled = %s, tax_bps = %s WHERE id = %s",
                        (
                            bool(venue.get("tax_enabled")),
                            int(venue.get("tax_bps") or 0),
                            existing["id"],
                        ),
                    )
                bundle = _load_order(existing["id"])
                assert bundle
            return order_out(bundle)

    origin = ORIGIN_BY_SPACE.get(space["kind"], "mostrador")
    option = dining_option or ("dine_in" if space["kind"] in {"table", "tab", "line"} else "takeout")
    covers = cover_count if mech["needs_cover_count"] else None
    queue_no = None
    if mech["needs_queue_number"] or space["kind"] == "kiosk":
        row = db.fetch_one(
            """
            SELECT COALESCE(MAX(queue_number), 0) + 1 AS n
            FROM orders
            WHERE venue_id = %s AND opened_at::date = CURRENT_DATE
            """,
            (venue["id"],),
        )
        queue_no = row["n"] if row else 1

    created = db.fetch_one(
        """
        INSERT INTO orders (
            venue_id, space_id, origin, status, cover_count, queue_number, dining_option,
            tax_enabled, tax_bps
        )
        VALUES (%s, %s, %s, 'open', %s, %s, %s, %s, %s)
        RETURNING *
        """,
        (
            venue["id"],
            space_id,
            origin,
            covers,
            queue_no,
            option,
            bool(venue.get("tax_enabled")),
            int(venue.get("tax_bps") or 0),
        ),
    )
    return order_out({"order": created, "items": [], "space": space})


def add_item(
    order_id: int,
    product_id: int,
    qty: int = 1,
    notes: str | None = None,
    modifier_ids: list[int] | None = None,
) -> dict:
    bundle = _load_order(order_id)
    if not bundle:
        raise ValueError("Orden no encontrada")
    if bundle["order"]["status"] in {"closed", "void"}:
        raise ValueError("La orden ya está cerrada")

    product = db.fetch_one("SELECT * FROM products WHERE id = %s", (product_id,))
    if not product or product["venue_id"] != bundle["order"]["venue_id"]:
        raise ValueError("Producto no encontrado")
    if not product["available"]:
        raise ValueError("Producto no disponible")

    origin = bundle["order"]["origin"]
    allowed = {
        "sala": product["sold_in_sala"],
        "barra": product["sold_in_barra"],
        "mostrador": product["sold_in_mostrador"],
        "kiosko": product["sold_in_sala"] or product["sold_in_barra"] or product["sold_in_mostrador"],
    }
    if not allowed.get(origin, True):
        raise ValueError(f"Ese producto no se vende en {origin}")

    chosen = []
    extra = 0
    for mid in modifier_ids or []:
        mod = db.fetch_one(
            "SELECT * FROM product_modifiers WHERE id = %s AND product_id = %s",
            (mid, product["id"]),
        )
        if not mod:
            raise ValueError("Modificador no válido")
        chosen.append(mod)
        extra += mod["price_delta_cents"] or 0
    unit = (product.get("price_cents") or 0) + extra
    created = db.fetch_one(
        """
        INSERT INTO order_items (
            order_id, product_id, name_snapshot, qty, station_id, status, notes, price_cents
        )
        VALUES (%s, %s, %s, %s, %s, 'queued', %s, %s)
        RETURNING id
        """,
        (
            order_id,
            product["id"],
            product["name"],
            max(1, qty),
            product.get("destination_station_id"),
            notes,
            unit,
        ),
    )
    for mod in chosen:
        db.execute(
            """
            INSERT INTO order_item_modifiers (item_id, name, price_delta_cents)
            VALUES (%s, %s, %s)
            """,
            (created["id"], mod["name"], mod["price_delta_cents"] or 0),
        )
    if bundle["order"]["status"] in {"sent", "in_progress", "ready"}:
        db.execute("UPDATE orders SET status = 'open' WHERE id = %s", (order_id,))
    loaded = _load_order(order_id)
    assert loaded
    return order_out(loaded)


def send_order(order_id: int) -> dict:
    bundle = _load_order(order_id)
    if not bundle:
        raise ValueError("Orden no encontrada")
    pending = [i for i in bundle["items"] if i["status"] == "queued"]
    if not pending:
        raise ValueError("No hay ítems nuevos para enviar")

    mech = mechanism_for(_profile())
    fulfillment = mech["fulfillment"]

    with db.connect() as conn:
        if fulfillment == "direct_handover":
            conn.execute(
                """
                UPDATE order_items
                SET status = 'served', sent_at = now(), ready_at = now()
                WHERE order_id = %s AND status = 'queued'
                """,
                (order_id,),
            )
            conn.execute(
                "UPDATE orders SET status = 'ready' WHERE id = %s",
                (order_id,),
            )
        elif fulfillment == "replenish_display_stations":
            conn.execute(
                """
                UPDATE order_items
                SET status = 'served', sent_at = now(), ready_at = now()
                WHERE order_id = %s AND status = 'queued'
                """,
                (order_id,),
            )
            conn.execute(
                "UPDATE orders SET status = 'sent' WHERE id = %s",
                (order_id,),
            )
        else:
            conn.execute(
                """
                UPDATE order_items
                SET sent_at = now()
                WHERE order_id = %s AND status = 'queued'
                """,
                (order_id,),
            )
            conn.execute(
                "UPDATE orders SET status = 'sent' WHERE id = %s",
                (order_id,),
            )

    loaded = _load_order(order_id)
    assert loaded
    return order_out(loaded)


def bump_item(item_id: int, action: str) -> dict:
    item = db.fetch_one("SELECT * FROM order_items WHERE id = %s", (item_id,))
    if not item:
        raise ValueError("Ítem no encontrado")

    if action == "prep":
        db.execute(
            "UPDATE order_items SET status = 'prep' WHERE id = %s",
            (item_id,),
        )
    elif action == "ready":
        db.execute(
            "UPDATE order_items SET status = 'ready', ready_at = now() WHERE id = %s",
            (item_id,),
        )
    elif action == "served":
        db.execute(
            "UPDATE order_items SET status = 'served' WHERE id = %s",
            (item_id,),
        )
    else:
        raise ValueError("Acción no válida")

    _refresh_order_status(item["order_id"])
    loaded = _load_order(item["order_id"])
    assert loaded
    return order_out(loaded)


def void_item(item_id: int) -> dict:
    item = db.fetch_one("SELECT * FROM order_items WHERE id = %s", (item_id,))
    if not item:
        raise ValueError("Ítem no encontrado")
    if item["status"] == "void":
        raise ValueError("El renglón ya está anulado")

    bundle = _load_order(item["order_id"])
    if not bundle:
        raise ValueError("Orden no encontrada")
    if bundle["order"]["status"] in {"closed", "void"}:
        raise ValueError("La orden está cerrada")
    if _has_payments(bundle["order"]["id"]):
        raise ValueError("Hay pagos en la cuenta")

    db.execute("UPDATE order_items SET status = 'void' WHERE id = %s", (item_id,))
    _close_if_empty(bundle["order"]["id"])
    loaded = _load_order(item["order_id"])
    assert loaded
    return order_out(loaded)


def _refresh_order_status(order_id: int) -> None:
    items = db.fetch_all(
        "SELECT status FROM order_items WHERE order_id = %s AND status <> 'void'",
        (order_id,),
    )
    if not items:
        return
    statuses = {i["status"] for i in items}
    if statuses <= {"served", "ready"}:
        next_status = "ready"
    elif "prep" in statuses or "ready" in statuses:
        next_status = "in_progress"
    elif any(i["status"] == "queued" and True for i in items):
        sent = db.fetch_one("SELECT sent_at FROM order_items WHERE order_id = %s AND sent_at IS NOT NULL", (order_id,))
        next_status = "sent" if sent else "open"
    else:
        next_status = "sent"
    db.execute("UPDATE orders SET status = %s WHERE id = %s AND status <> 'closed'", (next_status, order_id))


def _live_items(bundle: dict) -> list[dict]:
    return [i for i in bundle["items"] if i["status"] != "void"]


def deliver_order(order_id: int) -> dict:
    bundle = _load_order(order_id)
    if not bundle:
        raise ValueError("Orden no encontrada")
    order = bundle["order"]
    if order["status"] in {"closed", "void"}:
        raise ValueError("La orden ya está cerrada")
    live = _live_items(bundle)
    if not live:
        raise ValueError("No hay ítems para entregar")
    pending = [i for i in live if i["status"] in {"queued", "prep"}]
    if pending:
        raise ValueError("Todavía hay ítems en cocina o sin enviar")
    with db.connect() as conn:
        conn.execute(
            """
            UPDATE order_items
            SET status = 'served', ready_at = COALESCE(ready_at, now())
            WHERE order_id = %s AND status IN ('ready', 'served')
            """,
            (order_id,),
        )
        conn.execute(
            "UPDATE orders SET status = 'delivered' WHERE id = %s",
            (order_id,),
        )
    loaded = _load_order(order_id)
    assert loaded
    return order_out(loaded)


def close_order(order_id: int) -> dict:
    bundle = _load_order(order_id)
    if not bundle:
        raise ValueError("Orden no encontrada")
    order = bundle["order"]
    if order["status"] in {"closed", "void"}:
        raise ValueError("La orden ya está cerrada")
    if order["status"] not in {"ready", "delivered"}:
        raise ValueError("Solo se cierra cuando está lista o entregada")
    db.execute(
        "UPDATE orders SET status = 'closed', closed_at = now() WHERE id = %s",
        (order_id,),
    )
    loaded = _load_order(order_id)
    assert loaded
    return order_out(loaded)


def station_tickets(station_key: str) -> list[dict]:
    venue = _venue()
    rows = db.fetch_all(
        """
        SELECT i.id, i.name_snapshot, i.qty, i.status, i.notes, i.sent_at,
               o.id AS order_id, o.queue_number, o.origin, o.dining_option,
               sp.name AS space_name, s.key AS station_key, s.name AS station_name
        FROM order_items i
        JOIN orders o ON o.id = i.order_id
        JOIN stations s ON s.id = i.station_id
        LEFT JOIN spaces sp ON sp.id = o.space_id
        WHERE o.venue_id = %s
          AND s.key = %s
          AND i.sent_at IS NOT NULL
          AND i.status IN ('queued', 'prep', 'void')
        ORDER BY i.sent_at
        """,
        (venue["id"], station_key),
    )
    return [
        {
            "item_id": r["id"],
            "order_id": r["order_id"],
            "name": r["name_snapshot"],
            "qty": r["qty"],
            "status": r["status"],
            "notes": r["notes"],
            "queue_number": r["queue_number"],
            "space": r["space_name"],
            "dining_option": r.get("dining_option"),
            "dining_label": DINING_LABELS.get(r.get("dining_option") or ""),
            "station": r["station_key"],
            "sent_at": r["sent_at"].isoformat() if r.get("sent_at") else None,
            "modifiers": _item_mods(r["id"]),
        }
        for r in rows
    ]


def kds_board() -> dict:
    venue = _venue()
    mech = mechanism_for(_profile())
    stations = db.fetch_all(
        """
        SELECT * FROM stations
        WHERE venue_id = %s AND active AND kind IN ('kitchen', 'bar', 'expo', 'display')
        ORDER BY sort
        """,
        (venue["id"],),
    )
    return {
        "kitchen_mode": mech["kitchen_mode"],
        "fulfillment": mech["fulfillment"],
        "stations": [
            {
                "key": s["key"],
                "name": s["name"],
                "kind": s["kind"],
                "tickets": station_tickets(s["key"]),
            }
            for s in stations
        ],
    }


def _has_payments(order_id: int) -> bool:
    row = db.fetch_one(
        "SELECT COUNT(*) AS n FROM payments WHERE order_id = %s",
        (order_id,),
    )
    return bool(row and row["n"])


def _close_if_empty(order_id: int) -> None:
    live = db.fetch_all(
        "SELECT id FROM order_items WHERE order_id = %s AND status <> 'void'",
        (order_id,),
    )
    if live:
        _refresh_order_status(order_id)
        return
    db.execute(
        """
        UPDATE orders
        SET status = 'closed', closed_at = now()
        WHERE id = %s AND status <> 'closed'
        """,
        (order_id,),
    )


def _pair_out(source_id: int, dest_id: int) -> dict:
    source = _load_order(source_id)
    dest = _load_order(dest_id)
    return {
        "source": order_out(source) if source else None,
        "destination": order_out(dest) if dest else None,
    }


def _require_floor_space(space: dict | None) -> dict:
    if not space:
        raise ValueError("Espacio no encontrado")
    if space["kind"] not in FLOOR_KINDS:
        raise ValueError("Solo se mueve entre mesas o cuentas de barra")
    return space


def move_item(item_id: int, to_space_id: int) -> dict:
    item = db.fetch_one("SELECT * FROM order_items WHERE id = %s", (item_id,))
    if not item:
        raise ValueError("Ítem no encontrado")
    if item["status"] == "void":
        raise ValueError("No se mueve un ítem anulado")

    source = _load_order(item["order_id"])
    if not source:
        raise ValueError("Orden no encontrada")
    if source["order"]["status"] in {"closed", "void"}:
        raise ValueError("La orden origen está cerrada")
    _require_floor_space(source.get("space"))
    if _has_payments(source["order"]["id"]):
        raise ValueError("Hay pagos en la cuenta origen")

    dest_space = db.fetch_one(
        "SELECT * FROM spaces WHERE id = %s AND venue_id = %s",
        (to_space_id, source["order"]["venue_id"]),
    )
    _require_floor_space(dest_space)

    dest = open_order(to_space_id, source["order"].get("cover_count"), source["order"].get("dining_option"))
    if dest["id"] == source["order"]["id"]:
        raise ValueError("El destino es la misma cuenta")
    if dest["status"] in {"closed", "void"}:
        raise ValueError("La cuenta destino está cerrada")
    if _has_payments(dest["id"]):
        raise ValueError("Hay pagos en la cuenta destino")

    db.execute(
        "UPDATE order_items SET order_id = %s WHERE id = %s",
        (dest["id"], item_id),
    )
    _close_if_empty(source["order"]["id"])
    _refresh_order_status(dest["id"])
    return _pair_out(source["order"]["id"], dest["id"])


def merge_order(order_id: int, onto_order_id: int) -> dict:
    if order_id == onto_order_id:
        raise ValueError("No se junta una cuenta consigo misma")

    source = _load_order(order_id)
    dest = _load_order(onto_order_id)
    if not source or not dest:
        raise ValueError("Orden no encontrada")
    if source["order"]["status"] in {"closed", "void"}:
        raise ValueError("La orden origen está cerrada")
    if dest["order"]["status"] in {"closed", "void"}:
        raise ValueError("La cuenta destino está cerrada")
    _require_floor_space(source.get("space"))
    _require_floor_space(dest.get("space"))
    if _has_payments(order_id):
        raise ValueError("Hay pagos en la cuenta origen")
    if _has_payments(onto_order_id):
        raise ValueError("Hay pagos en la cuenta destino")

    live = _live_items(source)
    if not live:
        raise ValueError("La cuenta origen no tiene ítems")

    db.execute(
        """
        UPDATE order_items
        SET order_id = %s
        WHERE order_id = %s AND status <> 'void'
        """,
        (onto_order_id, order_id),
    )
    _close_if_empty(order_id)
    _refresh_order_status(onto_order_id)
    return _pair_out(order_id, onto_order_id)


def set_dining_option(order_id: int, dining_option: str) -> dict:
    bundle = _load_order(order_id)
    if not bundle:
        raise ValueError("Orden no encontrada")
    if bundle["order"]["status"] in {"closed", "void"}:
        raise ValueError("La orden está cerrada")
    if _has_payments(order_id):
        raise ValueError("Hay pagos en la cuenta")
    db.execute(
        "UPDATE orders SET dining_option = %s WHERE id = %s",
        (_dining(dining_option), order_id),
    )
    loaded = _load_order(order_id)
    assert loaded
    return order_out(loaded)


def set_discount(order_id: int, discount_type: str | None, value: int = 0) -> dict:
    bundle = _load_order(order_id)
    if not bundle:
        raise ValueError("Orden no encontrada")
    if bundle["order"]["status"] in {"closed", "void"}:
        raise ValueError("La orden está cerrada")
    if _has_payments(order_id):
        raise ValueError("Hay pagos en la cuenta")

    kind = (discount_type or "").strip().lower() or None
    if kind in {"none", "null"}:
        kind = None
    amount = int(value or 0)
    if amount < 0:
        raise ValueError("El descuento no puede ser negativo")
    if kind == "percent":
        if amount > 100:
            raise ValueError("El porcentaje no puede superar 100")
        if amount == 0:
            kind = None
    elif kind == "amount":
        if amount == 0:
            kind = None
    elif kind is None:
        amount = 0
    else:
        raise ValueError("Tipo de descuento no válido")

    db.execute(
        "UPDATE orders SET discount_type = %s, discount_value = %s WHERE id = %s",
        (kind, amount if kind else 0, order_id),
    )
    loaded = _load_order(order_id)
    assert loaded
    return order_out(loaded)


SYMBOLS = {"NIO": "C$", "USD": "$"}


def venue_public(venue: dict | None = None) -> dict:
    row = venue or _venue()
    code = (row.get("currency") or "NIO").strip().upper()
    if code not in SYMBOLS:
        code = "NIO"
    return {
        "id": row["id"],
        "name": row["name"],
        "slug": row["slug"],
        "tax_enabled": bool(row.get("tax_enabled")),
        "tax_bps": int(row.get("tax_bps") or 0),
        "currency": code,
        "symbol": SYMBOLS[code],
    }


def set_venue_tax(enabled: bool, bps: int = 1500) -> dict:
    return set_venue_config(tax_enabled=enabled, tax_bps=bps)


def set_venue_config(
    currency: str | None = None,
    tax_enabled: bool | None = None,
    tax_bps: int | None = None,
) -> dict:
    venue = _venue()
    if currency is not None:
        code = (currency or "").strip().upper()
        if code not in SYMBOLS:
            raise ValueError("Moneda no válida")
        db.execute("UPDATE venues SET currency = %s WHERE id = %s", (code, venue["id"]))
    if tax_enabled is not None or tax_bps is not None:
        on = bool(tax_enabled) if tax_enabled is not None else bool(venue.get("tax_enabled"))
        rate = max(0, min(10000, int(tax_bps if tax_bps is not None else venue.get("tax_bps") or 1500)))
        db.execute(
            "UPDATE venues SET tax_enabled = %s, tax_bps = %s WHERE id = %s",
            (on, rate, venue["id"]),
        )
        open_rows = db.fetch_all(
            "SELECT id FROM orders WHERE venue_id = %s AND status = ANY(%s)",
            (venue["id"], list(ACTIVE)),
        )
        for row in open_rows:
            if _has_payments(row["id"]):
                continue
            db.execute(
                "UPDATE orders SET tax_enabled = %s, tax_bps = %s WHERE id = %s",
                (on, rate, row["id"]),
            )
    return venue_public()


def modules_ok() -> list[str]:
    return resolve_modules(_profile(), settings.hermes_modules)
