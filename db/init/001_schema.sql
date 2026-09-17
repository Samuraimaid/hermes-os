-- Hermes OS schema 0.2.0
-- One catalog of tables. Venue profile decides which rows and rules apply.

CREATE TABLE IF NOT EXISTS hermes_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS venues (
    id              BIGSERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    slug            TEXT NOT NULL UNIQUE,
    profile         TEXT NOT NULL,
    modules         TEXT[] NOT NULL DEFAULT '{}',
    timezone        TEXT NOT NULL DEFAULT 'America/Managua',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS stations (
    id              BIGSERIAL PRIMARY KEY,
    venue_id        BIGINT NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    key             TEXT NOT NULL,
    name            TEXT NOT NULL,
    kind            TEXT NOT NULL,
    -- kitchen | bar | expo | counter | display
    sort            INT NOT NULL DEFAULT 0,
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (venue_id, key)
);

CREATE TABLE IF NOT EXISTS spaces (
    id              BIGSERIAL PRIMARY KEY,
    venue_id        BIGINT NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    key             TEXT NOT NULL,
    name            TEXT NOT NULL,
    kind            TEXT NOT NULL,
    -- table | tab | counter | queue | line
    zone            TEXT,
    capacity        INT,
    sort            INT NOT NULL DEFAULT 0,
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (venue_id, key)
);

CREATE TABLE IF NOT EXISTS products (
    id                      BIGSERIAL PRIMARY KEY,
    venue_id                BIGINT NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    sku                     TEXT,
    name                    TEXT NOT NULL,
    category                TEXT,
    price_cents             INT NOT NULL DEFAULT 0,
    destination_station_id  BIGINT REFERENCES stations(id) ON DELETE SET NULL,
    sold_in_sala            BOOLEAN NOT NULL DEFAULT FALSE,
    sold_in_barra           BOOLEAN NOT NULL DEFAULT FALSE,
    sold_in_mostrador       BOOLEAN NOT NULL DEFAULT TRUE,
    unlimited               BOOLEAN NOT NULL DEFAULT FALSE,
    available               BOOLEAN NOT NULL DEFAULT TRUE,
    sort                    INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS product_modifiers (
    id              BIGSERIAL PRIMARY KEY,
    product_id      BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    price_delta_cents INT NOT NULL DEFAULT 0,
    sort            INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS orders (
    id              BIGSERIAL PRIMARY KEY,
    venue_id        BIGINT NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    space_id        BIGINT REFERENCES spaces(id) ON DELETE SET NULL,
    origin          TEXT NOT NULL,
    -- sala | barra | mostrador
    status          TEXT NOT NULL DEFAULT 'open',
    -- open | sent | in_progress | ready | delivered | closed | void
    cover_count     INT,
    queue_number    INT,
    notes           TEXT,
    opened_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at       TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS order_items (
    id              BIGSERIAL PRIMARY KEY,
    order_id        BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id      BIGINT REFERENCES products(id) ON DELETE SET NULL,
    name_snapshot   TEXT NOT NULL,
    qty             INT NOT NULL DEFAULT 1,
    station_id      BIGINT REFERENCES stations(id) ON DELETE SET NULL,
    status          TEXT NOT NULL DEFAULT 'queued',
    -- queued | prep | ready | held | void | served
    notes           TEXT,
    sent_at         TIMESTAMPTZ,
    ready_at        TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_spaces_venue ON spaces (venue_id);
CREATE INDEX IF NOT EXISTS idx_stations_venue ON stations (venue_id);
CREATE INDEX IF NOT EXISTS idx_products_venue ON products (venue_id);
CREATE INDEX IF NOT EXISTS idx_orders_venue_status ON orders (venue_id, status);

INSERT INTO hermes_meta (key, value)
VALUES ('schema_version', '0.2.0')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
