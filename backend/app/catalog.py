from __future__ import annotations

from app import db
from app.orders import _venue
from app.serializers import product_out


def _load_product(product_id: int) -> dict | None:
    return db.fetch_one(
        """
        SELECT p.*, s.key AS station_key, s.name AS station_name
        FROM products p
        LEFT JOIN stations s ON s.id = p.destination_station_id
        WHERE p.id = %s
        """,
        (product_id,),
    )


def list_products() -> list[dict]:
    venue = _venue()
    rows = db.fetch_all(
        """
        SELECT p.*, s.key AS station_key, s.name AS station_name
        FROM products p
        LEFT JOIN stations s ON s.id = p.destination_station_id
        WHERE p.venue_id = %s
        ORDER BY p.sort, p.id
        """,
        (venue["id"],),
    )
    return [product_out(r) for r in rows]


def create_product(
    name: str,
    price_cents: int,
    category: str | None = None,
    destination_station_id: int | None = None,
) -> dict:
    venue = _venue()
    title = (name or "").strip()
    if not title:
        raise ValueError("El nombre es obligatorio")
    price = int(price_cents)
    if price < 0:
        raise ValueError("El precio no puede ser negativo")
    dest = destination_station_id or None
    if dest:
        st = db.fetch_one(
            "SELECT id FROM stations WHERE id = %s AND venue_id = %s",
            (dest, venue["id"]),
        )
        if not st:
            raise ValueError("Estación no encontrada")
    sort_row = db.fetch_one(
        "SELECT COALESCE(MAX(sort), 0) + 1 AS n FROM products WHERE venue_id = %s",
        (venue["id"],),
    )
    row = db.fetch_one(
        """
        INSERT INTO products (
            venue_id, name, category, price_cents, destination_station_id,
            sold_in_sala, sold_in_barra, sold_in_mostrador, available, sort
        )
        VALUES (%s, %s, %s, %s, %s, TRUE, FALSE, TRUE, TRUE, %s)
        RETURNING id
        """,
        (venue["id"], title, (category or "").strip() or None, price, dest, sort_row["n"]),
    )
    loaded = _load_product(row["id"])
    assert loaded
    return product_out(loaded)


def update_product(
    product_id: int,
    price_cents: int | None = None,
    available: bool | None = None,
) -> dict:
    venue = _venue()
    row = db.fetch_one(
        "SELECT * FROM products WHERE id = %s AND venue_id = %s",
        (product_id, venue["id"]),
    )
    if not row:
        raise ValueError("Artículo no encontrado")
    if price_cents is not None:
        price = int(price_cents)
        if price < 0:
            raise ValueError("El precio no puede ser negativo")
        db.execute("UPDATE products SET price_cents = %s WHERE id = %s", (price, product_id))
    if available is not None:
        db.execute("UPDATE products SET available = %s WHERE id = %s", (bool(available), product_id))
    loaded = _load_product(product_id)
    assert loaded
    return product_out(loaded)
