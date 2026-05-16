"""
SQLite database connection manager.
──────────────────────────────────────────────────────────────
Provides:
  • get_connection()  — raw SQLite connection (Row factory enabled)
  • get_db()          — context-manager that auto-commits / rolls back
  • execute_query()   — run a single SQL and fetch results
  • execute_many()    — run a single SQL with many param-sets
  • init_db()         — create all tables from schema.sql

Usage example:
    from database.connection import execute_query
    rows = execute_query("SELECT * FROM clients")
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager

# ─── optional: pretty logging (falls back to print if loguru not installed) ──
try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

import config  # <-- project-level config.py


# ════════════════════════════════════════════════════════════════════════
# LOW-LEVEL CONNECTION
# ════════════════════════════════════════════════════════════════════════

def get_connection() -> sqlite3.Connection:
    """
    Create a *new* SQLite connection every time.
    • row_factory = sqlite3.Row   → rows behave like dicts
    • WAL journal mode            → better concurrent read performance
    • foreign_keys ON             → enforce FK constraints
    """
    # Make sure parent directory exists
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(config.DB_PATH))
    conn.row_factory = sqlite3.Row           # row["column_name"] works
    conn.execute("PRAGMA journal_mode=WAL")  # write-ahead-log
    conn.execute("PRAGMA foreign_keys=ON")   # enforce FK relations
    return conn


# ════════════════════════════════════════════════════════════════════════
# CONTEXT MANAGER — auto commit / rollback
# ════════════════════════════════════════════════════════════════════════

@contextmanager
def get_db():
    """
    Usage:
        with get_db() as conn:
            conn.execute("INSERT INTO …", (…))
    On success the transaction is committed; on error it is rolled back.
    The connection is *always* closed afterwards.
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as exc:
        conn.rollback()
        logger.error(f"Database error (rolled back): {exc}")
        raise
    finally:
        conn.close()


# ════════════════════════════════════════════════════════════════════════
# SCHEMA INITIALISATION
# ════════════════════════════════════════════════════════════════════════

_db_initialised = False  # module-level flag so we only run once per process


def init_db():
    """
    Read schema.sql and execute it (CREATE TABLE IF NOT EXISTS …).
    Safe to call multiple times — it is guarded by a module-level flag
    and uses IF NOT EXISTS in the DDL.
    """
    global _db_initialised
    if _db_initialised:
        return

    schema_path = Path(__file__).parent / "schema.sql"
    if not schema_path.exists():
        logger.error(f"Schema file not found at {schema_path}")
        return

    schema_sql = schema_path.read_text(encoding="utf-8")

    # Use a raw connection (not the context-manager) because
    # executescript() issues its own implicit COMMIT.
    conn = get_connection()
    try:
        conn.executescript(schema_sql)
        logger.info("Database schema initialised successfully.")
    except Exception as exc:
        logger.error(f"Schema init failed: {exc}")
        raise
    finally:
        conn.close()

    _db_initialised = True


# ════════════════════════════════════════════════════════════════════════
# QUERY HELPERS
# ════════════════════════════════════════════════════════════════════════

def execute_query(query: str, params: tuple = (), fetch: str = "all"):
    """
    Execute ONE SQL statement and return the result.

    Parameters
    ----------
    query  : str    SQL with ? placeholders
    params : tuple  values to bind
    fetch  : str    "all"  → list[dict]
                    "one"  → dict | None
                    "none" → last-row-id (for INSERT / UPDATE)
    """
    with get_db() as conn:
        cursor = conn.execute(query, params)

        if fetch == "all":
            return [dict(row) for row in cursor.fetchall()]
        elif fetch == "one":
            row = cursor.fetchone()
            return dict(row) if row else None
        else:                         # "none"
            return cursor.lastrowid


def execute_many(query: str, params_list: list):
    """
    Execute the same SQL statement with many different param-tuples.
    Useful for bulk inserts.
    """
    with get_db() as conn:
        conn.executemany(query, params_list)
