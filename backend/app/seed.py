"""Create a generic demo venue that matches the active profile."""

from __future__ import annotations

from app import db
from app.mechanisms import mechanism_for
from app.profiles import PROFILES, resolve_modules
from app.settings import settings

LAYOUTS: dict[str, dict] = {
    "restaurant": {
        "stations": [
            ("cocina", "Cocina", "kitchen", 1),
            ("barra", "Barra", "bar", 2),
            ("expo", "Expedición", "expo", 3),
        ],
        "spaces": [
            ("mesa-1", "Mesa 1", "table", "Salón", 4, 1),
            ("mesa-2", "Mesa 2", "table", "Salón", 4, 2),
            ("mesa-3", "Mesa 3", "table", "Salón", 2, 3),
            ("mesa-4", "Mesa 4", "table", "Terraza", 4, 4),
        ],
        "products": [
            ("PLATO", "Plato del día", "Cocina", 18000, "cocina", True, False, False, False),
            ("BEB", "Bebida", "Barra", 6000, "barra", True, True, False, False),
            ("POSTRE", "Postre", "Cocina", 8000, "cocina", True, False, False, False),
        ],
    },
    "bar": {
        "stations": [
            ("bartender", "Bartender", "bar", 1),
            ("cocina", "Cocina de barra", "kitchen", 2),
        ],
        "spaces": [
            ("tab-1", "Taburete 1", "tab", "Barra", 1, 1),
            ("tab-2", "Taburete 2", "tab", "Barra", 1, 2),
            ("tab-3", "Taburete 3", "tab", "Barra", 1, 3),
            ("corrida", "Barra corrida", "tab", "Barra", 8, 4),
        ],
        "products": [
            ("TRAGO", "Trago de la casa", "Tragos", 12000, "bartender", False, True, False, False),
            ("CERVEZA", "Cerveza", "Tragos", 7000, "bartender", False, True, False, False),
            ("BOTANA", "Botana", "Cocina", 9000, "cocina", False, True, False, False),
        ],
    },
    "buffet": {
        "stations": [
            ("caliente", "Isla caliente", "display", 1),
            ("fria", "Isla fría", "display", 2),
            ("postres", "Postres", "display", 3),
            ("caja", "Caja de paso", "counter", 4),
        ],
        "spaces": [
            ("linea-caliente", "Línea caliente", "line", "Buffet", None, 1),
            ("linea-fria", "Línea fría", "line", "Buffet", None, 2),
            ("linea-postres", "Línea postres", "line", "Buffet", None, 3),
        ],
        "products": [
            ("CAL", "Bandeja caliente", "Islas", 0, "caliente", False, False, True, True),
            ("FRIA", "Bandeja fría", "Islas", 0, "fria", False, False, True, True),
            ("POS", "Bandeja de postres", "Islas", 0, "postres", False, False, True, True),
        ],
    },
    "qsr": {
        "stations": [
            ("cocina", "Cocina", "kitchen", 1),
            ("expo", "Ventanilla", "expo", 2),
        ],
        "spaces": [
            ("mostrador", "Mostrador", "counter", "Frente", None, 1),
            ("cola", "Cola de turnos", "queue", "Frente", None, 2),
        ],
        "products": [
            ("COMBO", "Combo", "Mostrador", 15000, "cocina", False, False, True, False),
            ("EXTRA", "Extra", "Mostrador", 3000, "cocina", False, False, True, False),
        ],
    },
    "convenience": {
        "stations": [],
        "spaces": [
            ("caja-1", "Caja 1", "counter", "Tienda", None, 1),
        ],
        "products": [
            ("SKU-1", "Artículo A", "Anaquel", 2500, None, False, False, True, False),
            ("SKU-2", "Artículo B", "Anaquel", 4000, None, False, False, True, False),
            ("LISTO", "Listo para llevar", "Comida", 6500, None, False, False, True, False),
        ],
    },
}


def ensure_demo_venue() -> dict | None:
    if not db.available():
        return None

    profile = settings.hermes_profile.strip().lower()
    if profile not in PROFILES:
        profile = "restaurant"
    modules = resolve_modules(profile, settings.hermes_modules)
    layout = LAYOUTS[profile]
    mech = mechanism_for(profile)

    venue = db.fetch_one("SELECT * FROM venues WHERE slug = %s", (settings.venue_slug,))
    if not venue:
        venue = db.fetch_one(
            """
            INSERT INTO venues (name, slug, profile, modules)
            VALUES (%s, %s, %s, %s)
            RETURNING *
            """,
            (settings.venue_name, settings.venue_slug, profile, modules),
        )
    else:
        db.execute(
            "UPDATE venues SET profile = %s, modules = %s, name = %s WHERE id = %s",
            (profile, modules, settings.venue_name, venue["id"]),
        )
        venue = db.fetch_one("SELECT * FROM venues WHERE id = %s", (venue["id"],))

    vid = venue["id"]
    existing_stations = db.fetch_all("SELECT key FROM stations WHERE venue_id = %s", (vid,))
    if not existing_stations:
        for key, name, kind, sort in layout["stations"]:
            db.execute(
                """
                INSERT INTO stations (venue_id, key, name, kind, sort)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (vid, key, name, kind, sort),
            )

    existing_spaces = db.fetch_all("SELECT key FROM spaces WHERE venue_id = %s", (vid,))
    if not existing_spaces:
        for key, name, kind, zone, cap, sort in layout["spaces"]:
            db.execute(
                """
                INSERT INTO spaces (venue_id, key, name, kind, zone, capacity, sort)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (vid, key, name, kind, zone, cap, sort),
            )

    existing_products = db.fetch_all("SELECT id FROM products WHERE venue_id = %s", (vid,))
    if not existing_products:
        stations = {
            r["key"]: r["id"]
            for r in db.fetch_all("SELECT id, key FROM stations WHERE venue_id = %s", (vid,))
        }
        for sku, name, cat, price, dest, sala, barra, mostrador, unlimited in layout["products"]:
            dest_id = stations.get(dest) if dest else None
            db.execute(
                """
                INSERT INTO products (
                    venue_id, sku, name, category, price_cents,
                    destination_station_id, sold_in_sala, sold_in_barra,
                    sold_in_mostrador, unlimited
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (vid, sku, name, cat, price, dest_id, sala, barra, mostrador, unlimited),
            )

    return {
        "venue": venue,
        "mechanism": mech,
        "stations": db.fetch_all(
            "SELECT * FROM stations WHERE venue_id = %s ORDER BY sort", (vid,)
        ),
        "spaces": db.fetch_all(
            "SELECT * FROM spaces WHERE venue_id = %s ORDER BY sort", (vid,)
        ),
        "products": db.fetch_all(
            """
            SELECT p.*, s.key AS station_key, s.name AS station_name
            FROM products p
            LEFT JOIN stations s ON s.id = p.destination_station_id
            WHERE p.venue_id = %s
            ORDER BY p.sort, p.id
            """,
            (vid,),
        ),
    }
