"""Idempotent column upgrades for venues that already ran 0.2.0."""

from app import db

STATEMENTS = [
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS dining_option TEXT",
    "ALTER TABLE order_items ADD COLUMN IF NOT EXISTS price_cents INT NOT NULL DEFAULT 0",
    """
    INSERT INTO hermes_meta (key, value) VALUES ('schema_version', '0.3.0')
    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """,
]


def apply() -> None:
    if not db.available():
        return
    with db.connect() as conn:
        for sql in STATEMENTS:
            conn.execute(sql)
