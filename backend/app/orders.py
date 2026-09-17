from __future__ import annotations

from app import db
from app.mechanisms import mechanism_for
from app.profiles import PROFILES, resolve_modules
from app.settings import settings

ACTIVE = ("open", "sent", "in_progress", "ready", "delivered")

ORIGIN_BY_SPACE = {
    "table": "sala",
    "tab": "barra",
    "counter": "mostrador",
    "queue": "mostrador",
    "line": "mostrador",
}


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
    return {
        "id": order["id"],
        "status": order["status"],
        "origin": order["origin"],
        "dining_option": order.get("dining_option"),
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
            }
            for i in items
        ],
        "precuenta": {
            "item_count": sum(i["qty"] for i in items if i["status"] != "void"),
            "subtotal_cents": subtotal,
        },
        "paid_cents": paid,
        "due_cents": max(0, subtotal - paid),
    }


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
        return order_out(bundle)

    origin = ORIGIN_BY_SPACE.get(space["kind"], "mostrador")
    option = dining_option or ("dine_in" if space["kind"] in {"table", "tab", "line"} else "takeout")
    covers = cover_count if mech["needs_cover_count"] else None
    queue_no = None
    if mech["needs_queue_number"]:
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
            venue_id, space_id, origin, status, cover_count, queue_number, dining_option
        )
        VALUES (%s, %s, %s, 'open', %s, %s, %s)
        RETURNING *
        """,
        (venue["id"], space_id, origin, covers, queue_no, option),
    )
    return order_out({"order": created, "items": [], "space": space})


def add_item(order_id: int, product_id: int, qty: int = 1, notes: str | None = None) -> dict:
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
    }
    if not allowed.get(origin, True):
        raise ValueError(f"Ese producto no se vende en {origin}")

    db.fetch_one(
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
            product.get("price_cents") or 0,
        ),
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
               o.id AS order_id, o.queue_number, o.origin,
               sp.name AS space_name, s.key AS station_key, s.name AS station_name
        FROM order_items i
        JOIN orders o ON o.id = i.order_id
        JOIN stations s ON s.id = i.station_id
        LEFT JOIN spaces sp ON sp.id = o.space_id
        WHERE o.venue_id = %s
          AND s.key = %s
          AND i.sent_at IS NOT NULL
          AND i.status IN ('queued', 'prep')
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
            "station": r["station_key"],
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


def modules_ok() -> list[str]:
    return resolve_modules(_profile(), settings.hermes_modules)
