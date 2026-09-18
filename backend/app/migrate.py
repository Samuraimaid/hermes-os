"""Idempotent column upgrades for venues that already ran 0.2.0."""

from app import db

STATEMENTS = [
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS dining_option TEXT",
    "ALTER TABLE order_items ADD COLUMN IF NOT EXISTS price_cents INT NOT NULL DEFAULT 0",
    """
    INSERT INTO hermes_meta (key, value) VALUES ('schema_version', '0.3.0')
    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """,
    """
    CREATE TABLE IF NOT EXISTS cash_shifts (
        id BIGSERIAL PRIMARY KEY,
        venue_id BIGINT NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
        status TEXT NOT NULL DEFAULT 'open',
        opening_cash_cents INT NOT NULL DEFAULT 0,
        counted_cash_cents INT,
        opened_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        closed_at TIMESTAMPTZ
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS payments (
        id BIGSERIAL PRIMARY KEY,
        shift_id BIGINT NOT NULL REFERENCES cash_shifts(id) ON DELETE CASCADE,
        order_id BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
        method TEXT NOT NULL,
        amount_cents INT NOT NULL,
        tip_cents INT NOT NULL DEFAULT 0,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    INSERT INTO hermes_meta (key, value) VALUES ('schema_version', '0.4.0')
    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """,
    """
    CREATE TABLE IF NOT EXISTS staff (
        id BIGSERIAL PRIMARY KEY,
        venue_id BIGINT NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        pin_hash TEXT NOT NULL,
        active BOOLEAN NOT NULL DEFAULT TRUE
    )
    """,
    """
    INSERT INTO hermes_meta (key, value) VALUES ('schema_version', '0.5.0')
    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """,
    """
    CREATE TABLE IF NOT EXISTS order_item_modifiers (
        id BIGSERIAL PRIMARY KEY,
        item_id BIGINT NOT NULL REFERENCES order_items(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        price_delta_cents INT NOT NULL DEFAULT 0
    )
    """,
    """
    INSERT INTO hermes_meta (key, value) VALUES ('schema_version', '0.6.0')
    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """,
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS discount_type TEXT",
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS discount_value INT NOT NULL DEFAULT 0",
    """
    INSERT INTO hermes_meta (key, value) VALUES ('schema_version', '0.7.0')
    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """,
    "ALTER TABLE venues ADD COLUMN IF NOT EXISTS tax_percent INT NOT NULL DEFAULT 16",
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS tax_percent INT",
    """
    INSERT INTO hermes_meta (key, value) VALUES ('schema_version', '0.8.0')
    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """,
    "ALTER TABLE venues ADD COLUMN IF NOT EXISTS tax_enabled BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE venues ADD COLUMN IF NOT EXISTS tax_bps INT NOT NULL DEFAULT 1500",
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS tax_enabled BOOLEAN",
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS tax_bps INT",
    """
    INSERT INTO hermes_meta (key, value) VALUES ('schema_version', '0.9.0')
    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """,
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS refunded_at TIMESTAMPTZ",
    """
    CREATE TABLE IF NOT EXISTS refunds (
        id BIGSERIAL PRIMARY KEY,
        shift_id BIGINT NOT NULL REFERENCES cash_shifts(id) ON DELETE CASCADE,
        order_id BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
        method TEXT NOT NULL,
        amount_cents INT NOT NULL,
        tip_cents INT NOT NULL DEFAULT 0,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    INSERT INTO hermes_meta (key, value) VALUES ('schema_version', '0.10.0')
    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """,
    "ALTER TABLE venues ADD COLUMN IF NOT EXISTS currency TEXT NOT NULL DEFAULT 'NIO'",
    """
    INSERT INTO hermes_meta (key, value) VALUES ('schema_version', '0.11.0')
    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """,
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS guest_name TEXT",
    """
    INSERT INTO hermes_meta (key, value) VALUES ('schema_version', '0.12.0')
    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """,
]


def apply() -> None:
    if not db.available():
        return
    with db.connect() as conn:
        for sql in STATEMENTS:
            conn.execute(sql)
