"""Search history in SQLite: what was searched, when, and for how much."""

import os
import sqlite3
from datetime import datetime, timezone

from sneaker_bot.services.price_format import format_amount

# Inside Docker the volume is mounted at /app/data; locally the same folder is
# used, so both ways of running share one history.
DEFAULT_PATH = os.getenv("DB_PATH", os.path.join("data", "bot.db"))

_SCHEMA = """
CREATE TABLE IF NOT EXISTS searches (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    query      TEXT    NOT NULL,
    brand      TEXT    NOT NULL DEFAULT '',
    model      TEXT    NOT NULL DEFAULT '',
    size       TEXT    NOT NULL DEFAULT '',
    found      INTEGER NOT NULL DEFAULT 0,
    min_price  REAL,
    created_at TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_searches_user ON searches(user_id, id DESC);
"""


def _connect(path: str | None = None) -> sqlite3.Connection:
    target = path or DEFAULT_PATH
    parent = os.path.dirname(os.path.abspath(target))
    if parent:
        os.makedirs(parent, exist_ok=True)
    connection = sqlite3.connect(target, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.executescript(_SCHEMA)
    return connection


def init(path: str | None = None) -> None:
    """Create the schema; safe to call on every start."""
    with _connect(path) as connection:
        connection.execute("SELECT 1")


def save_search(
    user_id: int,
    query: str,
    brand: str = "",
    model: str = "",
    size: str = "",
    found: int = 0,
    min_price: float | None = None,
    path: str | None = None,
) -> int:
    """Remember one completed search and return its id."""
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with _connect(path) as connection:
        cursor = connection.execute(
            "INSERT INTO searches (user_id, query, brand, model, size, found, min_price, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, query, brand, model, size, found, min_price, created),
        )
        return int(cursor.lastrowid)


def recent(user_id: int, limit: int = 8, path: str | None = None) -> list[dict]:
    """The latest searches of one user, newest first."""
    with _connect(path) as connection:
        rows = connection.execute(
            "SELECT * FROM searches WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def by_id(search_id: int, path: str | None = None) -> dict | None:
    with _connect(path) as connection:
        row = connection.execute(
            "SELECT * FROM searches WHERE id = ?", (search_id,)
        ).fetchone()
    return dict(row) if row else None


def previous_min(user_id: int, query: str, path: str | None = None) -> float | None:
    """The cheapest price the same query produced last time, if any."""
    with _connect(path) as connection:
        row = connection.execute(
            "SELECT min_price FROM searches"
            " WHERE user_id = ? AND query = ? AND min_price IS NOT NULL"
            " ORDER BY id DESC LIMIT 1",
            (user_id, query),
        ).fetchone()
    return float(row["min_price"]) if row else None


def clear(user_id: int, path: str | None = None) -> int:
    """Forget everything this user searched for; returns the number of rows."""
    with _connect(path) as connection:
        cursor = connection.execute(
            "DELETE FROM searches WHERE user_id = ?", (user_id,)
        )
        return int(cursor.rowcount or 0)


def label(entry: dict) -> str:
    """One line for the history keyboard."""
    created = entry.get("created_at") or ""
    try:
        moment = datetime.fromisoformat(created).astimezone()
        stamp = moment.strftime("%d.%m")
    except (TypeError, ValueError):
        stamp = ""

    query = (entry.get("query") or "").strip() or "без названия"
    found = entry.get("found") or 0
    parts = [f"🕓 {stamp} · {query}" if stamp else f"🕓 {query}"]

    if found:
        parts.append(f"{found} шт")
    if entry.get("min_price") is not None:
        parts.append(f"от {format_amount(entry['min_price'])}")
    if not found:
        parts.append("ничего не найдено")
    return " · ".join(parts)
