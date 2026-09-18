from __future__ import annotations

import hashlib
import secrets

from app import db
from app.settings import settings

ROLES = {
    "owner": {"floor", "kds", "cash", "kiosk", "admin"},
    "waiter": {"floor"},
    "kitchen": {"kds"},
    "cashier": {"cash", "floor"},
    "kiosk": {"kiosk"},
}

DEMO = (
    ("Dueño", "owner", "0000"),
    ("Mesero", "waiter", "1111"),
    ("Cocina", "kitchen", "2222"),
    ("Cajero", "cashier", "3333"),
    ("Kiosco", "kiosk", "4444"),
)

_tokens: dict[str, dict] = {}


def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()


def _venue_id() -> int | None:
    row = db.fetch_one("SELECT id FROM venues WHERE slug = %s", (settings.venue_slug,))
    return row["id"] if row else None


def ensure_users() -> None:
    if not db.available():
        return
    vid = _venue_id()
    if not vid:
        return
    for name, role, pin in DEMO:
        found = db.fetch_one(
            "SELECT id FROM staff WHERE venue_id = %s AND role = %s",
            (vid, role),
        )
        if found:
            continue
        db.execute(
            """
            INSERT INTO staff (venue_id, name, role, pin_hash, active)
            VALUES (%s, %s, %s, %s, TRUE)
            """,
            (vid, name, role, hash_pin(pin)),
        )


def user_out(row: dict, token: str | None = None) -> dict:
    payload = {
        "id": row["id"],
        "name": row["name"],
        "role": row["role"],
        "caps": sorted(ROLES.get(row["role"], set())),
    }
    if token:
        payload["token"] = token
    return payload


def login(pin: str) -> dict:
    vid = _venue_id()
    if not vid:
        raise ValueError("No hay local")
    pin = (pin or "").strip()
    row = db.fetch_one(
        """
        SELECT * FROM staff
        WHERE venue_id = %s AND pin_hash = %s AND active
        """,
        (vid, hash_pin(pin)),
    )
    if not row:
        raise ValueError("PIN incorrecto")
    token = secrets.token_hex(16)
    _tokens[token] = row
    return user_out(row, token)


def resolve(token: str | None) -> dict | None:
    if not token:
        return None
    key = token.removeprefix("Bearer ").strip()
    return _tokens.get(key)


def logout(token: str | None) -> None:
    if not token:
        return
    _tokens.pop(token.removeprefix("Bearer ").strip(), None)


def cap_for_path(method: str, path: str) -> str | None:
    if path in {
        "/health",
        "/api/login",
        "/api/instance",
        "/api/logout",
        "/api/cds",
        "/docs",
        "/openapi.json",
    }:
        return None
    if not path.startswith("/api/"):
        return None
    path = path.rstrip("/") or "/"
    if path.startswith("/api/shift") or path.endswith("/pay") or "/balance" in path:
        return "cash"
    if path.startswith("/api/kds") or path.startswith("/api/stations"):
        return "kds"
    if path.startswith("/api/items/") and path.endswith("/bump"):
        return "kds"
    if path.startswith("/api/staff") or path.startswith("/api/sales") or path.startswith("/api/venue"):
        return "admin"
    return "floor"


def allow(user: dict | None, cap: str | None) -> bool:
    if cap is None:
        return True
    if not user:
        return False
    have = ROLES.get(user["role"], set())
    if "admin" in have:
        return True
    if cap in have:
        return True
    return cap == "floor" and "kiosk" in have
