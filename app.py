"""
The Tunes backend: a small REST API built with Flask.

Every route calls one function in queries.py (that's where YOUR SQL goes).
You don't need to edit this file, but read a few routes to see how an HTTP
request becomes a function call, then a SQL query, then JSON for the frontend.

Start the server:
    python app.py
Then open http://localhost:5001
"""

import os
import sqlite3
import time

from flask import Flask, jsonify, request, send_from_directory

import db
import seed

# Instructor demo mode: WORKSHOP_SOLUTIONS=1 python app.py
if os.environ.get("WORKSHOP_SOLUTIONS") == "1":
    import solutions as queries
    print("*** Running with the ANSWER KEY (solutions.py) ***")
else:
    import queries

app = Flask(__name__, static_folder="static")
app.json.sort_keys = False  # keep columns in the order your SELECT lists them


def respond(function, *args, success_status=200):
    """
    Calls a function from queries.py and turns the result into JSON.
    Every response includes the SQL that ran, so the app's SQL log can show it.
    """
    db.reset_last_sql()
    started = time.perf_counter()
    debug_info = {"function": f"queries.{function.__name__}()"}

    try:
        result = function(*args)
    except db.NotImplementedYet:
        return jsonify({
            **debug_info,
            "error": "not_implemented",
            "message": f"{function.__name__}() isn't written yet. Add the SQL in queries.py.",
        }), 501
    except sqlite3.IntegrityError as error:
        # e.g. a FOREIGN KEY or UNIQUE / PRIMARY KEY rule blocked the change
        return jsonify({**debug_info, "error": "integrity", "message": str(error), "sql": db.last_sql()}), 409
    except sqlite3.Error as error:
        return jsonify({**debug_info, "error": "sql", "message": str(error), "sql": db.last_sql()}), 400

    debug_info["sql"] = db.last_sql()
    debug_info["ms"] = round((time.perf_counter() - started) * 1000, 1)

    if result is None:
        return jsonify({**debug_info, "error": "not_found", "message": "Not found"}), 404
    return jsonify({**debug_info, "data": result}), success_status


# =====================================================================
# Artists
# =====================================================================

@app.get("/api/artists")
def list_artists():
    return respond(queries.list_artists)


@app.post("/api/artists")
def create_artist():
    body = request.get_json()
    return respond(queries.create_artist, body["name"], body["country"], int(body["formed_year"]),
                   success_status=201)


@app.get("/api/artists/<int:artist_id>")
def get_artist(artist_id):
    return respond(queries.get_artist, artist_id)


@app.put("/api/artists/<int:artist_id>")
def update_artist(artist_id):
    body = request.get_json()
    return respond(queries.update_artist, artist_id, body["name"], body["country"], int(body["formed_year"]))


@app.delete("/api/artists/<int:artist_id>")
def delete_artist(artist_id):
    return respond(queries.delete_artist, artist_id)


@app.get("/api/artists/<int:artist_id>/songs")
def get_artist_songs(artist_id):
    return respond(queries.get_artist_songs, artist_id)


# =====================================================================
# Albums
# =====================================================================

@app.get("/api/albums")
def list_albums():
    return respond(queries.list_albums)


# =====================================================================
# Songs
# =====================================================================

@app.get("/api/songs")
def list_songs():
    search_term = request.args.get("q", "").strip()
    genre = request.args.get("genre", "").strip()

    if search_term:
        return respond(queries.search_songs, search_term)
    if genre:
        return respond(queries.get_songs_by_genre, genre)
    return respond(queries.list_songs)


@app.get("/api/genres")
def list_genres():
    return respond(queries.list_genres)


@app.post("/api/songs")
def create_song():
    body = request.get_json()
    return respond(queries.create_song, int(body["album_id"]), body["title"], body["genre"],
                   int(body["duration_sec"]), success_status=201)


@app.put("/api/songs/<int:song_id>")
def update_song(song_id):
    body = request.get_json()
    return respond(queries.update_song, song_id, body["title"], body["genre"], int(body["duration_sec"]))


@app.delete("/api/songs/<int:song_id>")
def delete_song(song_id):
    return respond(queries.delete_song, song_id)


@app.post("/api/songs/<int:song_id>/play")
def record_play(song_id):
    body = request.get_json()
    return respond(queries.record_play, int(body["user_id"]), song_id, success_status=201)


# =====================================================================
# Playlists
# =====================================================================

@app.get("/api/playlists")
def list_playlists():
    return respond(queries.list_playlists)


@app.post("/api/playlists")
def create_playlist():
    body = request.get_json()
    return respond(queries.create_playlist, int(body["user_id"]), body["name"], success_status=201)


@app.patch("/api/playlists/<int:playlist_id>")
def rename_playlist(playlist_id):
    body = request.get_json()
    return respond(queries.rename_playlist, playlist_id, body["name"])


@app.delete("/api/playlists/<int:playlist_id>")
def delete_playlist(playlist_id):
    return respond(queries.delete_playlist, playlist_id)


@app.get("/api/playlists/<int:playlist_id>/songs")
def get_playlist_songs(playlist_id):
    return respond(queries.get_playlist_songs, playlist_id)


@app.post("/api/playlists/<int:playlist_id>/songs")
def add_song_to_playlist(playlist_id):
    body = request.get_json()
    return respond(queries.add_song_to_playlist, playlist_id, int(body["song_id"]), success_status=201)


@app.delete("/api/playlists/<int:playlist_id>/songs/<int:song_id>")
def remove_song_from_playlist(playlist_id, song_id):
    return respond(queries.remove_song_from_playlist, playlist_id, song_id)


# =====================================================================
# Users
# =====================================================================

@app.get("/api/users")
def list_users():
    return respond(queries.list_users)


@app.get("/api/users/inactive")
def get_inactive_users():
    return respond(queries.get_inactive_users)


# =====================================================================
# Charts
# =====================================================================

@app.get("/api/charts/top-songs")
def get_top_songs():
    limit = int(request.args.get("limit", 10))
    return respond(queries.get_top_songs, limit)


@app.get("/api/charts/genres")
def get_genre_stats():
    return respond(queries.get_genre_stats)


@app.get("/api/charts/prolific-artists")
def get_prolific_artists():
    min_songs = int(request.args.get("min_songs", 20))
    return respond(queries.get_prolific_artists, min_songs)


@app.get("/api/charts/genre-leaders")
def get_genre_leaders():
    return respond(queries.get_genre_leaders)


# =====================================================================
# Dev tools: database schema viewer + reset (already written, no SQL needed from you)
# =====================================================================

@app.get("/api/dev/schema")
def schema():
    connection = db.get_connection()
    tables = []
    table_rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY rowid").fetchall()
    for table_row in table_rows:
        table_name = table_row["name"]
        columns = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        foreign_keys = connection.execute(f"PRAGMA foreign_key_list({table_name})").fetchall()
        row_count = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

        references = {}  # e.g. {"artist_id": "artists.id"}
        for foreign_key in foreign_keys:
            references[foreign_key["from"]] = f"{foreign_key['table']}.{foreign_key['to']}"

        column_info = []
        for column in columns:
            column_info.append({
                "name": column["name"],
                "type": column["type"],
                "pk": bool(column["pk"]),
                "references": references.get(column["name"]),
            })
        tables.append({"name": table_name, "row_count": row_count, "columns": column_info})
    connection.close()
    return jsonify(tables)


@app.post("/api/dev/query")
def free_play_query():
    """Run a read-only SQL statement typed into the Free play page."""
    sql = ((request.get_json(silent=True) or {}).get("sql") or "").strip().rstrip(";").strip()
    if not sql:
        return jsonify({"error": "Type a SELECT statement first."}), 400
    if ";" in sql:
        return jsonify({"error": "Run one statement at a time."}), 400
    if sql.split(None, 1)[0].upper() not in ("SELECT", "WITH", "PRAGMA", "EXPLAIN"):
        return jsonify({"error": "Free play is read-only: start your statement with SELECT."}), 400

    # Open the file read-only so nothing typed here can change the data.
    connection = sqlite3.connect(f"file:{db.DEFAULT_DB_PATH}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    limit = 500
    try:
        started = time.time()
        cursor = connection.execute(sql)
        rows = cursor.fetchmany(limit + 1)
        columns = [d[0] for d in cursor.description] if cursor.description else []
        truncated = len(rows) > limit
        rows = [list(r) for r in rows[:limit]]
        ms = round((time.time() - started) * 1000, 1)
    except sqlite3.Error as error:
        return jsonify({"error": str(error)}), 400
    finally:
        connection.close()
    return jsonify({"columns": columns, "rows": rows, "truncated": truncated, "limit": limit, "ms": ms})


@app.post("/api/dev/reset")
def reset_database():
    seed.build_database()
    return jsonify({"message": "Database reset to the original data."})


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    if not db.DEFAULT_DB_PATH.exists():
        seed.build_database()
        print("Created data/tunes.db")
    app.run(debug=True, port=5001)
