def space_out(row: dict) -> dict:
    return {
        "id": row["id"],
        "key": row["key"],
        "name": row["name"],
        "kind": row["kind"],
        "zone": row.get("zone"),
        "capacity": row.get("capacity"),
    }


def station_out(row: dict) -> dict:
    return {
        "id": row["id"],
        "key": row["key"],
        "name": row["name"],
        "kind": row["kind"],
    }


def product_out(row: dict) -> dict:
    from app import db

    mods = db.fetch_all(
        """
        SELECT id, name, price_delta_cents
        FROM product_modifiers WHERE product_id = %s ORDER BY sort, id
        """,
        (row["id"],),
    )
    return {
        "id": row["id"],
        "sku": row.get("sku"),
        "name": row["name"],
        "category": row.get("category"),
        "price_cents": row["price_cents"],
        "station": row.get("station_key"),
        "sold_in": {
            "sala": row["sold_in_sala"],
            "barra": row["sold_in_barra"],
            "mostrador": row["sold_in_mostrador"],
        },
        "unlimited": row["unlimited"],
        "available": row["available"],
        "modifiers": [
            {"id": m["id"], "name": m["name"], "price_delta_cents": m["price_delta_cents"]}
            for m in mods
        ],
    }
