"""
Database helpers. You don't need to edit this file —
but it's worth reading so you know what run_query(), run_query_one() and run_write() do.
"""

import sqlite3
import textwrap
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).parent / "data" / "tunes.db"

# The test suite temporarily points queries at a scratch copy of the database
# (so testing your INSERT/UPDATE/DELETE never touches the real data).
_active_db_path = ContextVar("active_db_path", default=DEFAULT_DB_PATH)

# The last SQL statement that ran, so the app's SQL log can show it to you.
_last_sql = ContextVar("last_sql", default=None)


class NotImplementedYet(Exception):
    """Raised when an exercise still has its placeholder SQL."""


def get_connection():
    connection = sqlite3.connect(_active_db_path.get())
    connection.row_factory = sqlite3.Row          # rows behave like dicts
    connection.execute("PRAGMA foreign_keys = ON")  # makes ON DELETE CASCADE work
    return connection


def _check_sql_written(sql):
    """Treat SQL that is empty or only comments as 'not done yet'."""
    meaningful_lines = []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("--"):
            meaningful_lines.append(stripped)
    if not meaningful_lines:
        raise NotImplementedYet()


def run_query(sql, params=()):
    """
    Run a SELECT and return the results as a list of dicts, e.g.
        [{"id": 1, "name": "Luna Vega"}, {"id": 2, "name": "Static Bloom"}]
    """
    _check_sql_written(sql)
    _last_sql.set(textwrap.dedent(sql).strip())
    connection = get_connection()
    try:
        cursor = connection.execute(sql, params)
        rows = [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()
    return rows


def run_query_one(sql, params=()):
    """
    Run a SELECT that should return ONE row (e.g. "the artist with id 3").
    Returns that row as a dict, or None if nothing matched.
    """
    rows = run_query(sql, params)
    if len(rows) == 0:
        return None
    return rows[0]


def run_write(sql, params=()):
    """
    Run an INSERT, UPDATE or DELETE and save (commit) the change.
    Returns:
        new_id         -> id of the row you just inserted (INSERT only)
        rows_affected  -> how many rows were inserted/updated/deleted
    """
    _check_sql_written(sql)
    _last_sql.set(textwrap.dedent(sql).strip())
    connection = get_connection()
    try:
        cursor = connection.execute(sql, params)
        connection.commit()
        is_insert = sql.strip().upper().startswith("INSERT")
        result = {
            "new_id": cursor.lastrowid if is_insert else None,
            "rows_affected": cursor.rowcount,
        }
    finally:
        connection.close()
    return result


def last_sql():
    return _last_sql.get()


def reset_last_sql():
    _last_sql.set(None)


@contextmanager
def using_database(path):
    """Temporarily run every query against a different database file."""
    token = _active_db_path.set(path)
    try:
        yield
    finally:
        _active_db_path.reset(token)
