"""
core/db.py
---------------
Lightweight SQLite bridge for FocusWell.

This module handles database initialization and provides simple
helpers for executing and querying data without exposing raw SQL
to the rest of the app.

Responsibilities:
- Create `focuswell.db` if it doesn't exist
- Ensure required columns exist (due_date, due_time)
- Provide helper functions for CRUD operations
"""

import os
import sqlite3
from typing import Iterable

# ------------------------------------------------------------
# Database path (one level above /core)
# ------------------------------------------------------------
_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "focuswell.db")
_DB_PATH = os.path.normpath(_DB_PATH)

# ------------------------------------------------------------
# Connection helper
# ------------------------------------------------------------
def get_connection() -> sqlite3.Connection:
    """
    Returns a live SQLite connection with foreign keys enabled.
    """
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ------------------------------------------------------------
# Ensure optional columns (due_date / due_time)
# ------------------------------------------------------------
def _ensure_due_date_column(conn: sqlite3.Connection) -> None:
    """Add 'due_date' column if missing (TEXT ISO 'YYYY-MM-DD')."""
    cur = conn.execute("PRAGMA table_info(tasks)")
    cols = [row[1] for row in cur.fetchall()]
    if "due_date" not in cols:
        conn.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT")
        conn.commit()

def _ensure_due_time_column(conn: sqlite3.Connection) -> None:
    """Add 'due_time' column if missing (TEXT 'HH:MM')."""
    cur = conn.execute("PRAGMA table_info(tasks)")
    cols = [row[1] for row in cur.fetchall()]
    if "due_time" not in cols:
        conn.execute("ALTER TABLE tasks ADD COLUMN due_time TEXT")
        conn.commit()

# ------------------------------------------------------------
# Database initialization
# ------------------------------------------------------------
def init_db() -> None:
    """Creates the tasks table if it doesn't exist and ensures columns."""
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT (datetime('now')),
                updated_at TIMESTAMP
            )
            """
        )
        conn.commit()
        _ensure_due_date_column(conn)
        _ensure_due_time_column(conn)
    finally:
        conn.close()

# ------------------------------------------------------------
# CRUD helpers
# ------------------------------------------------------------
def execute(sql: str, params: Iterable = ()) -> int:
    """
    Execute INSERT / UPDATE / DELETE and return lastrowid (or 0).
    """
    conn = get_connection()
    try:
        cur = conn.execute(sql, tuple(params))
        conn.commit()
        return cur.lastrowid or 0
    finally:
        conn.close()

def query_all(sql: str, params: Iterable = ()) -> list[tuple]:
    """
    Execute SELECT and return all rows as a list of tuples.
    """
    conn = get_connection()
    try:
        cur = conn.execute(sql, tuple(params))
        rows = cur.fetchall()
        return rows
    finally:
        conn.close()
