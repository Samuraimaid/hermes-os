from __future__ import annotations

from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from app.settings import settings


def available() -> bool:
    return bool(settings.database_url)


@contextmanager
def connect():
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not set")
    conn = psycopg.connect(settings.database_url, row_factory=dict_row)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_all(sql: str, params=None) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(sql, params or ()).fetchall()
        return [dict(r) for r in rows]


def fetch_one(sql: str, params=None) -> dict | None:
    with connect() as conn:
        row = conn.execute(sql, params or ()).fetchone()
        return dict(row) if row else None


def execute(sql: str, params=None):
    with connect() as conn:
        return conn.execute(sql, params or ())
