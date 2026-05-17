from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


@contextmanager
def get_connection(database_path: str | Path) -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(str(database_path))
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db(database_path: str | Path) -> None:
    with get_connection(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversion_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                base_currency TEXT NOT NULL,
                quote_currency TEXT NOT NULL,
                converted_amount REAL NOT NULL,
                converted_amount_display TEXT NOT NULL,
                rate REAL NOT NULL,
                rate_display TEXT NOT NULL,
                provider TEXT NOT NULL,
                is_stale INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS alert_subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                base_currency TEXT NOT NULL,
                quote_currency TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(email, base_currency, quote_currency)
            );

            CREATE INDEX IF NOT EXISTS idx_conversion_history_created_at
            ON conversion_history(created_at DESC);

            CREATE INDEX IF NOT EXISTS idx_alert_subscribers_pair
            ON alert_subscribers(base_currency, quote_currency);
            """
        )


def record_conversion(
    database_path: str | Path,
    *,
    amount: float,
    base_currency: str,
    quote_currency: str,
    converted_amount: float,
    converted_amount_display: str,
    rate: float,
    rate_display: str,
    provider: str,
    is_stale: bool,
) -> None:
    with get_connection(database_path) as connection:
        connection.execute(
            """
            INSERT INTO conversion_history (
                amount,
                base_currency,
                quote_currency,
                converted_amount,
                converted_amount_display,
                rate,
                rate_display,
                provider,
                is_stale
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                amount,
                base_currency,
                quote_currency,
                converted_amount,
                converted_amount_display,
                rate,
                rate_display,
                provider,
                1 if is_stale else 0,
            ),
        )


def fetch_recent_history(database_path: str | Path, limit: int = 6) -> list[sqlite3.Row]:
    with get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            SELECT
                amount,
                base_currency,
                quote_currency,
                converted_amount,
                converted_amount_display,
                rate,
                rate_display,
                provider,
                is_stale,
                created_at
            FROM conversion_history
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return cursor.fetchall()


def register_alert_subscription(
    database_path: str | Path,
    *,
    email: str,
    base_currency: str,
    quote_currency: str,
) -> bool:
    try:
        with get_connection(database_path) as connection:
            connection.execute(
                """
                INSERT INTO alert_subscribers (email, base_currency, quote_currency)
                VALUES (?, ?, ?)
                """,
                (email, base_currency, quote_currency),
            )
        return True
    except sqlite3.IntegrityError:
        return False
