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


def _sku(value: str | None) -> str | None:
    text = (value or "").strip()
    return text or None


def create_product(
    name: str,
    price_cents: int,
    category: str | None = None,
    destination_station_id: int | None = None,
    sku: str | None = None,
    track_stock: bool = False,
    stock_quantity: float = 0.0,
    low_stock_threshold: float | None = None,
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
            venue_id, sku, name, category, price_cents, destination_station_id,
            sold_in_sala, sold_in_barra, sold_in_mostrador, available, sort,
            track_stock, stock_quantity, low_stock_threshold
        )
        VALUES (%s, %s, %s, %s, %s, %s, TRUE, FALSE, TRUE, TRUE, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            venue["id"],
            _sku(sku),
            title,
            (category or "").strip() or None,
            price,
            dest,
            sort_row["n"],
            bool(track_stock),
            float(stock_quantity or 0.0),
            float(low_stock_threshold) if low_stock_threshold is not None else None,
        ),
    )
    loaded = _load_product(row["id"])
    assert loaded
    return product_out(loaded)


def update_product(
    product_id: int,
    price_cents: int | None = None,
    available: bool | None = None,
    sku: str | None = None,
    name: str | None = None,
    category: str | None = None,
    track_stock: bool | None = None,
    stock_quantity: float | None = None,
    low_stock_threshold: float | None = None,
) -> dict:
    venue = _venue()
    row = db.fetch_one(
        "SELECT * FROM products WHERE id = %s AND venue_id = %s",
        (product_id, venue["id"]),
    )
    if not row:
        raise ValueError("Artículo no encontrado")
    if name is not None:
        title = name.strip()
        if not title:
            raise ValueError("El nombre no puede estar vacío")
        db.execute("UPDATE products SET name = %s WHERE id = %s", (title, product_id))
    if category is not None:
        cat = category.strip() or None
        db.execute("UPDATE products SET category = %s WHERE id = %s", (cat, product_id))
    if price_cents is not None:
        price = int(price_cents)
        if price < 0:
            raise ValueError("El precio no puede ser negativo")
        db.execute("UPDATE products SET price_cents = %s WHERE id = %s", (price, product_id))
    if available is not None:
        db.execute("UPDATE products SET available = %s WHERE id = %s", (bool(available), product_id))
    if sku is not None:
        db.execute("UPDATE products SET sku = %s WHERE id = %s", (_sku(sku), product_id))
    if track_stock is not None:
        db.execute("UPDATE products SET track_stock = %s WHERE id = %s", (bool(track_stock), product_id))
    if stock_quantity is not None:
        db.execute("UPDATE products SET stock_quantity = %s WHERE id = %s", (float(stock_quantity), product_id))
    if low_stock_threshold is not None:
        val = float(low_stock_threshold) if low_stock_threshold >= 0 else None
        db.execute("UPDATE products SET low_stock_threshold = %s WHERE id = %s", (val, product_id))
    loaded = _load_product(product_id)
    assert loaded
    return product_out(loaded)


def add_modifier(product_id: int, name: str, price_delta_cents: int = 0) -> dict:
    venue = _venue()
    prod = db.fetch_one("SELECT * FROM products WHERE id = %s AND venue_id = %s", (product_id, venue["id"]))
    if not prod:
        raise ValueError("Artículo no encontrado")
    mod_name = (name or "").strip()
    if not mod_name:
        raise ValueError("El nombre del modificador es obligatorio")
    delta = int(price_delta_cents)
    sort_row = db.fetch_one(
        "SELECT COALESCE(MAX(sort), 0) + 1 AS n FROM product_modifiers WHERE product_id = %s",
        (product_id,),
    )
    row = db.fetch_one(
        """
        INSERT INTO product_modifiers (product_id, name, price_delta_cents, sort)
        VALUES (%s, %s, %s, %s)
        RETURNING id, product_id, name, price_delta_cents
        """,
        (product_id, mod_name, delta, sort_row["n"]),
    )
    return row


def delete_modifier(modifier_id: int) -> dict:
    venue = _venue()
    row = db.fetch_one(
        """
        SELECT m.id, m.product_id FROM product_modifiers m
        JOIN products p ON p.id = m.product_id
        WHERE m.id = %s AND p.venue_id = %s
        """,
        (modifier_id, venue["id"]),
    )
    if not row:
        raise ValueError("Modificador no encontrado")
    db.execute("DELETE FROM product_modifiers WHERE id = %s", (modifier_id,))
    return {"deleted": True, "id": modifier_id, "product_id": row["product_id"]}

