"""
Compares a function from queries.py against the answer key and explains what's different.
Every test runs on scratch copies of the database, so your real data is never touched.
"""

import shutil
import sqlite3
import tempfile
from pathlib import Path

import db
import solutions


def _normalize(value):
    if isinstance(value, float):
        return round(value, 2)
    return value


def _as_row_list(result):
    """run_query_one returns a dict or None; turn everything into a list of rows."""
    if result is None:
        return []
    if isinstance(result, dict):
        return [result]
    return result


def _rows_as_tuples(rows, columns):
    return [tuple(_normalize(row.get(column)) for column in columns) for row in rows]


def _sort_key(row_tuple):
    return tuple((value is None, str(value)) for value in row_tuple)


def compare_rows(expected, actual, order_matters):
    """Returns (passed, message)."""
    if len(actual) == 0 and len(expected) > 0:
        return False, f"Your query returned 0 rows, but {len(expected)} were expected."
    if len(expected) == 0 and len(actual) == 0:
        return True, "OK"

    expected_columns = list(expected[0].keys()) if expected else []
    actual_columns = list(actual[0].keys())
    if set(expected_columns) != set(actual_columns):
        return False, (
            f"Column names don't match.\n"
            f"Expected:     {', '.join(expected_columns)}\n"
            f"You returned: {', '.join(actual_columns)}\n"
            f"Tip: use AS to rename a column, e.g. albums.title AS album"
        )

    expected_tuples = _rows_as_tuples(expected, expected_columns)
    actual_tuples = _rows_as_tuples(actual, expected_columns)

    if len(expected_tuples) != len(actual_tuples):
        return False, (
            f"Expected {len(expected_tuples)} rows, but your query returned {len(actual_tuples)}.\n"
            f"Check your WHERE / JOIN / GROUP BY / LIMIT."
        )

    same_rows_any_order = sorted(expected_tuples, key=_sort_key) == sorted(actual_tuples, key=_sort_key)
    if expected_tuples == actual_tuples:
        return True, "OK"
    if same_rows_any_order:
        if order_matters:
            return False, "Right rows, wrong order. Check your ORDER BY."
        return True, "OK"

    for row in expected_tuples:
        if row not in actual_tuples:
            missing = dict(zip(expected_columns, row))
            return False, f"Same number of rows, but this expected row is missing:\n{missing}"
    return False, "The rows don't match the expected result."


def _make_scratch_copy(folder, name, setup_sql):
    path = Path(folder) / name
    shutil.copy(db.DEFAULT_DB_PATH, path)
    connection = sqlite3.connect(path)
    for sql in setup_sql:
        connection.execute(sql)
    connection.commit()
    connection.close()
    return path


def _snapshot(database_path, verify_sql):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    snapshots = [[dict(row) for row in connection.execute(sql).fetchall()] for sql in verify_sql]
    connection.close()
    return snapshots


def _run_test(test, student_module, scratch_dir):
    setup_sql = test.get("setup_sql", [])
    answer_db = _make_scratch_copy(scratch_dir, "answer.db", setup_sql)
    student_db = _make_scratch_copy(scratch_dir, "student.db", setup_sql)
    function_name = test["function"]
    args = test["args"]

    with db.using_database(answer_db):
        expected = getattr(solutions, function_name)(*args)
    with db.using_database(student_db):
        actual = getattr(student_module, function_name)(*args)

    if test["kind"] == "read":
        return compare_rows(_as_row_list(expected), _as_row_list(actual), test["order_matters"])

    if actual["rows_affected"] != expected["rows_affected"]:
        return False, (
            f"Your statement changed {actual['rows_affected']} row(s), but it should change "
            f"{expected['rows_affected']}.\nDid you forget a WHERE clause, or mix up the order of the ? params?"
        )
    expected_tables = _snapshot(answer_db, test["verify_sql"])
    actual_tables = _snapshot(student_db, test["verify_sql"])
    for verify_sql, expected_rows, actual_rows in zip(test["verify_sql"], expected_tables, actual_tables):
        if expected_rows != actual_rows:
            table_name = verify_sql.split("FROM")[1].split()[0]
            return False, f"After your statement, the `{table_name}` table doesn't look right."
    return True, "OK"


def run_test(test, student_module):
    """Returns {"status": "pass" | "fail" | "todo" | "error", "message": str}."""
    with tempfile.TemporaryDirectory() as scratch_dir:
        try:
            passed, message = _run_test(test, student_module, scratch_dir)
        except db.NotImplementedYet:
            return {"status": "todo", "message": "Not written yet"}
        except sqlite3.Error as error:
            return {"status": "error", "message": f"SQL error: {error}"}
    return {"status": "pass" if passed else "fail", "message": message}
