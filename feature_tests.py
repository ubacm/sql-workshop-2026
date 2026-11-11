"""
Test cases for every function in queries.py, grouped by page of the app.
check_all.py runs these and compares your results with the answer key.

read  tests: compare the rows your query returns.
write tests: run your INSERT/UPDATE/DELETE on a scratch copy of the database,
             then compare the affected tables (verify_sql) with the answer key's.
             setup_sql runs first, to put the scratch copy in a known state.
"""

TESTS = [
    # ---------------- Artists ----------------
    {"page": "Artists", "function": "list_artists", "kind": "read", "args": [], "order_matters": True},
    {"page": "Artists", "function": "get_artist", "kind": "read", "args": [3], "order_matters": True},
    {"page": "Artists", "function": "get_artist_songs", "kind": "read", "args": [10], "order_matters": True},
    {
        "page": "Artists", "function": "create_artist", "kind": "write",
        "args": ["Test Band", "USA", 2024],
        "verify_sql": ["SELECT * FROM artists ORDER BY id"],
    },
    {
        "page": "Artists", "function": "update_artist", "kind": "write",
        "args": [1, "Renamed Band", "UK", 2001],
        "verify_sql": ["SELECT * FROM artists ORDER BY id"],
    },
    {
        "page": "Artists", "function": "delete_artist", "kind": "write",
        "args": [999],
        "setup_sql": ["INSERT INTO artists (id, name, country, formed_year) VALUES (999, 'Temp', 'USA', 2020)"],
        "verify_sql": ["SELECT * FROM artists ORDER BY id"],
    },

    # ---------------- Songs ----------------
    {"page": "Songs", "function": "list_genres", "kind": "read", "args": [], "order_matters": True},
    {"page": "Songs", "function": "list_songs", "kind": "read", "args": [], "order_matters": True},
    {"page": "Songs", "function": "get_songs_by_genre", "kind": "read", "args": ["Rock"], "order_matters": True},
    {"page": "Songs", "function": "search_songs", "kind": "read", "args": ["love"], "order_matters": True},
    {"page": "Songs", "function": "search_songs", "kind": "read", "args": ["luna"], "order_matters": True},
    {
        "page": "Songs", "function": "create_song", "kind": "write",
        "args": [1, "Test Song", "Pop", 200],
        "verify_sql": ["SELECT id, album_id, title, genre, duration_sec FROM songs ORDER BY id"],
    },
    {
        "page": "Songs", "function": "update_song", "kind": "write",
        "args": [1, "Edited Song", "Jazz", 199],
        "verify_sql": ["SELECT id, album_id, title, genre, duration_sec FROM songs ORDER BY id"],
    },
    {
        "page": "Songs", "function": "delete_song", "kind": "write",
        "args": [5],
        "verify_sql": [
            "SELECT id FROM songs ORDER BY id",
            "SELECT id FROM plays ORDER BY id",
            "SELECT playlist_id, song_id FROM playlist_songs ORDER BY playlist_id, song_id",
        ],
    },
    {
        "page": "Songs", "function": "record_play", "kind": "write",
        "args": [1, 3],
        "verify_sql": ["SELECT id, user_id, song_id FROM plays ORDER BY id"],
    },

    # ---------------- Users ----------------
    {"page": "Users", "function": "list_users", "kind": "read", "args": [], "order_matters": True},
    {"page": "Users", "function": "get_inactive_users", "kind": "read", "args": [], "order_matters": True},

    # ---------------- Playlists ----------------
    {"page": "Playlists", "function": "get_playlist_songs", "kind": "read", "args": [1], "order_matters": True},
    {
        "page": "Playlists", "function": "create_playlist", "kind": "write",
        "args": [1, "Test Mix"],
        "verify_sql": ["SELECT id, user_id, name FROM playlists ORDER BY id"],
    },
    {
        "page": "Playlists", "function": "rename_playlist", "kind": "write",
        "args": [1, "Renamed Mix"],
        "verify_sql": ["SELECT id, user_id, name FROM playlists ORDER BY id"],
    },
    {
        "page": "Playlists", "function": "delete_playlist", "kind": "write",
        "args": [2],
        "verify_sql": [
            "SELECT id, user_id, name FROM playlists ORDER BY id",
            "SELECT playlist_id, song_id FROM playlist_songs ORDER BY playlist_id, song_id",
        ],
    },
    {
        "page": "Playlists", "function": "add_song_to_playlist", "kind": "write",
        "args": [1, 2],
        "setup_sql": ["DELETE FROM playlist_songs WHERE playlist_id = 1 AND song_id = 2"],
        "verify_sql": ["SELECT playlist_id, song_id FROM playlist_songs ORDER BY playlist_id, song_id"],
    },
    {
        "page": "Playlists", "function": "remove_song_from_playlist", "kind": "write",
        "args": [1, 3],
        "setup_sql": [
            "INSERT OR IGNORE INTO playlist_songs (playlist_id, song_id) VALUES (1, 3)",
            "INSERT OR IGNORE INTO playlist_songs (playlist_id, song_id) VALUES (2, 3)",
        ],
        "verify_sql": ["SELECT playlist_id, song_id FROM playlist_songs ORDER BY playlist_id, song_id"],
    },
    {"page": "Playlists", "function": "list_playlists", "kind": "read", "args": [], "order_matters": True,
     "setup_sql": ["INSERT INTO playlists (id, user_id, name) VALUES (999, 1, 'Empty One')"]},

    # ---------------- Charts ----------------
    {"page": "Charts", "function": "get_genre_stats", "kind": "read", "args": [], "order_matters": True},
    {"page": "Charts", "function": "get_top_songs", "kind": "read", "args": [10], "order_matters": True},
    {"page": "Charts", "function": "get_prolific_artists", "kind": "read", "args": [20], "order_matters": True},
    {"page": "Charts", "function": "get_genre_leaders", "kind": "read", "args": [], "order_matters": True},
]
