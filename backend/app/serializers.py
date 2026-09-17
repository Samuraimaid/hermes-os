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
    }
