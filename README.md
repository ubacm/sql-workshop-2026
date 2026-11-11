# ♪ Tunes: build the data layer of a music app

Tunes is a full-stack CRUD app: a Flask REST API, a SQLite database full of data,
and a frontend for browsing songs, artists, playlists, charts and users.

**It's missing its SQL.** Every API route calls a function in `queries.py`, and almost all
of them say `-- TODO`. Until you write the query, that part of the app shows
** Not implemented yet**. Write the SQL, save, refresh, and the feature works.

## Setup

You need **Python 3.9+** (SQLite comes with it).

```bash
cd sql-workshop
pip install -r requirements.txt
python app.py
```

Open **http://localhost:5001**. The database builds itself on first run.

## Workflow

1. Click around the app and find something that says *Not implemented yet*.
2. Open `queries.py`, find that function, and read its docstring (columns, order, route).
3. Replace `-- TODO` with SQL. Use `?` placeholders; the params tuple is already written.
4. Save, refresh the page, and use the feature.
5. Open the **SQL log** (top right) to see every request, the function it called, and the SQL that ran.
6. Run the tests:

```bash
python check_all.py            # everything
python check_all.py playlist   # only functions with "playlist" in the name
```

The **Database** page shows every table with its foreign keys (what you JOIN on), and has
a **Reset database** button for when you've deleted something you wanted.

## What you'll build

| Page | Functions | SQL you'll use |
|------|-----------|----------------|
| Artists | `list_artists`, `get_artist`, `create_artist`, `update_artist`, `delete_artist`, `get_artist_songs` | SELECT, WHERE, INSERT, UPDATE, DELETE, JOIN |
| Songs | `list_genres`, `list_songs`, `get_songs_by_genre`, `search_songs`, `create_song`, `update_song`, `delete_song`, `record_play` | DISTINCT, multi-table JOIN, LIKE, OR |
| Users | `list_users`, `get_inactive_users` | LEFT JOIN + IS NULL |
| Playlists | `get_playlist_songs`, `create_playlist`, `rename_playlist`, `delete_playlist`, `add_song_to_playlist`, `remove_song_from_playlist`, `list_playlists` | Junction tables, composite keys, LEFT JOIN + GROUP BY |
| Charts | `get_genre_stats`, `get_top_songs`, `get_prolific_artists`, `get_genre_leaders` | GROUP BY, COUNT/AVG, HAVING, CTEs, window functions |

`list_albums()` is already written as an example. The top of `queries.py` suggests a build order with difficulty ratings.

Things worth trying once the features work:
- Delete an artist who has albums. The FOREIGN KEY blocks it. Then create a new artist and delete that one.
- Add the same song to a playlist twice. The PRIMARY KEY blocks it.
- Hit ▶ on a song a bunch of times and watch it climb the Charts.
- Leave the `WHERE` off `update_artist` and see what happens (then hit Reset database 😅).

## Files

| File | What it is |
|------|------------|
| `queries.py` | **The data layer. Your SQL goes here.** |
| `schema.sql` | Every table, column and constraint |
| `app.py` | REST API routes: read these to see how requests reach your functions |
| `db.py` | `run_query()`, `run_query_one()`, `run_write()` helpers |
| `seed.py` | Builds `data/tunes.db` with fake data (`python seed.py` resets it) |
| `check_all.py`, `checker.py`, `feature_tests.py` | Test suite |
| `solutions.py` | Answer key 🙈 |
| `static/` | Frontend (plain HTML/CSS/JS) |

---
