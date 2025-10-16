# tests/conftest.py
import sqlite3
import pytest
import core.db as db

# --- Keep a master shared in-memory DB alive for the whole session ---
@pytest.fixture(scope="session", autouse=True)
def shared_memory_master():
    uri = "file:focuswell_test?mode=memory&cache=shared"
    master = sqlite3.connect(uri, uri=True, check_same_thread=False)
    master.execute("PRAGMA foreign_keys = ON")
    yield {"uri": uri, "master": master}
    try:
        master.close()
    except Exception:
        pass

# --- For each test: patch get_connection() to open NEW conns to the same DB,
#     ensure schema, and start from a clean tasks table. ---
@pytest.fixture(autouse=True)
def patch_db_and_clean(monkeypatch, shared_memory_master):
    uri = shared_memory_master["uri"]

    def _new_connection():
        conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # All core.db calls will use a fresh connection to the shared in-memory DB
    monkeypatch.setattr(db, "get_connection", _new_connection, raising=True)

    # Ensure schema exists (idempotent)
    db.init_db()

    # Clean table so tests don't affect each other
    conn = _new_connection()
    try:
        conn.execute("DELETE FROM tasks")
        conn.commit()
    finally:
        conn.close()

    yield
