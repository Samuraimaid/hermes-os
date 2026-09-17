"""Venue profiles and default modules."""

from __future__ import annotations

PROFILES: dict[str, dict] = {
    "restaurant": {
        "label": "Restaurante",
        "modules": ["sala", "cocina", "caja", "pantallas"],
    },
    "bar": {
        "label": "Bar",
        "modules": ["barra", "cocina", "caja", "pantallas"],
    },
    "buffet": {
        "label": "Buffet",
        "modules": ["mostrador", "cocina", "caja", "pantallas"],
    },
    "qsr": {
        "label": "Comida rápida",
        "modules": ["mostrador", "cocina", "caja", "pantallas"],
    },
    "convenience": {
        "label": "Convivencia",
        "modules": ["mostrador", "caja", "pantallas"],
    },
}

ALL_MODULES = ("sala", "barra", "cocina", "mostrador", "pantallas", "caja")


def resolve_modules(profile: str, raw_modules: str | None) -> list[str]:
    key = (profile or "restaurant").strip().lower()
    if key not in PROFILES:
        key = "restaurant"
    if raw_modules and raw_modules.strip():
        wanted = [m.strip().lower() for m in raw_modules.split(",") if m.strip()]
        return [m for m in wanted if m in ALL_MODULES]
    return list(PROFILES[key]["modules"])
