"""
Persistence layer (Load). Stores products and their price history
in SQLite.
"""
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from config import DB_PATH

logger = logging.getLogger(__name__)


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """Creates the tables if they don't exist yet. Idempotent."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                price REAL NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
            """
        )
        conn.commit()
    logger.info("Database initialized at %s", DB_PATH)


def get_or_create_product(name: str, url: str) -> int:
    """Returns the product's id, creating it first if needed."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM products WHERE url = ?", (url,))
        row = cursor.fetchone()
        if row:
            return row[0]

        cursor.execute(
            "INSERT INTO products (name, url) VALUES (?, ?)", (name, url)
        )
        conn.commit()
        logger.info("New product registered: %s (%s)", name, url)
        return cursor.lastrowid


def save_price(product_id: int, price: float) -> None:
    """Inserts a new price reading with its UTC timestamp."""
    timestamp = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO price_history (product_id, price, timestamp) "
            "VALUES (?, ?, ?)",
            (product_id, price, timestamp),
        )
        conn.commit()
    logger.info("Price saved: product_id=%s price=%.2f", product_id, price)


def get_last_price(product_id: int) -> float | None:
    """Returns the most recently recorded price, or None if there isn't one yet.

    IMPORTANT: call this BEFORE save_price() so you can compare the new
    price against the previous one.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT price FROM price_history
            WHERE product_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (product_id,),
        )
        row = cursor.fetchone()
        return row[0] if row else None

