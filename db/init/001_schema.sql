-- Hermes OS — schema placeholder.
-- Tables for venues, users, catalog, orders and stations land here.

CREATE TABLE IF NOT EXISTS hermes_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

INSERT INTO hermes_meta (key, value)
VALUES ('schema_version', '0.1.0')
ON CONFLICT (key) DO NOTHING;
