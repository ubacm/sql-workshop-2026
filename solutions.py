"""
ANSWER KEY — instructors only.
`python check_all.py` compares queries.py against this file.
Demo the finished app with:  WORKSHOP_SOLUTIONS=1 python app.py
"""

from db import run_query, run_query_one, run_write


# =====================================================================
# ARTISTS
# =====================================================================

def list_artists():
    sql = """
        SELECT id, name, country, formed_year
        FROM artists
        ORDER BY name
    """
    return run_query(sql)


def get_artist(artist_id):
    sql = """
        SELECT id, name, country, formed_year
        FROM artists
        WHERE id = ?
    """
    return run_query_one(sql, (artist_id,))


def get_artist_songs(artist_id):
    sql = """
        SELECT songs.id, songs.title, albums.title AS album, songs.genre, songs.duration_sec
        FROM songs
        JOIN albums ON albums.id = songs.album_id
        WHERE albums.artist_id = ?
        ORDER BY album, songs.title
    """
    return run_query(sql, (artist_id,))


def create_artist(name, country, formed_year):
    sql = """
        INSERT INTO artists (name, country, formed_year)
        VALUES (?, ?, ?)
    """
    return run_write(sql, (name, country, formed_year))


def update_artist(artist_id, name, country, formed_year):
    sql = """
        UPDATE artists
        SET name = ?, country = ?, formed_year = ?
        WHERE id = ?
    """
    return run_write(sql, (name, country, formed_year, artist_id))


def delete_artist(artist_id):
    sql = """
        DELETE FROM artists
        WHERE id = ?
    """
    return run_write(sql, (artist_id,))


# =====================================================================
# ALBUMS
# =====================================================================

def list_albums():
    sql = """
        SELECT albums.id, albums.title, albums.release_year, artists.name AS artist
        FROM albums
        JOIN artists ON artists.id = albums.artist_id
        ORDER BY artists.name, albums.release_year
    """
    return run_query(sql)


# =====================================================================
# SONGS
# =====================================================================

def list_songs():
    sql = """
        SELECT songs.id, songs.title, songs.genre, songs.duration_sec,
               albums.title AS album, artists.name AS artist
        FROM songs
        JOIN albums  ON albums.id  = songs.album_id
        JOIN artists ON artists.id = albums.artist_id
        ORDER BY artist, songs.title
    """
    return run_query(sql)


def search_songs(term):
    sql = """
        SELECT songs.id, songs.title, songs.genre, songs.duration_sec,
               albums.title AS album, artists.name AS artist
        FROM songs
        JOIN albums  ON albums.id  = songs.album_id
        JOIN artists ON artists.id = albums.artist_id
        WHERE songs.title LIKE '%' || ? || '%'
           OR artists.name LIKE '%' || ? || '%'
        ORDER BY artist, songs.title
    """
    return run_query(sql, (term, term))


def list_genres():
    sql = """
        SELECT DISTINCT genre
        FROM songs
        ORDER BY genre
    """
    return run_query(sql)


def get_songs_by_genre(genre):
    sql = """
        SELECT songs.id, songs.title, songs.genre, songs.duration_sec,
               albums.title AS album, artists.name AS artist
        FROM songs
        JOIN albums  ON albums.id  = songs.album_id
        JOIN artists ON artists.id = albums.artist_id
        WHERE songs.genre = ?
        ORDER BY artist, songs.title
    """
    return run_query(sql, (genre,))


def create_song(album_id, title, genre, duration_sec):
    sql = """
        INSERT INTO songs (album_id, title, genre, duration_sec)
        VALUES (?, ?, ?, ?)
    """
    return run_write(sql, (album_id, title, genre, duration_sec))


def update_song(song_id, title, genre, duration_sec):
    sql = """
        UPDATE songs
        SET title = ?, genre = ?, duration_sec = ?
        WHERE id = ?
    """
    return run_write(sql, (title, genre, duration_sec, song_id))


def delete_song(song_id):
    sql = """
        DELETE FROM songs
        WHERE id = ?
    """
    return run_write(sql, (song_id,))


def record_play(user_id, song_id):
    sql = """
        INSERT INTO plays (user_id, song_id)
        VALUES (?, ?)
    """
    return run_write(sql, (user_id, song_id))


# =====================================================================
# PLAYLISTS
# =====================================================================

def list_playlists():
    sql = """
        SELECT playlists.id,
               playlists.name,
               users.username AS owner,
               COUNT(playlist_songs.song_id) AS song_count
        FROM playlists
        JOIN users ON users.id = playlists.user_id
        LEFT JOIN playlist_songs ON playlist_songs.playlist_id = playlists.id
        GROUP BY playlists.id
        ORDER BY playlists.name, playlists.id
    """
    return run_query(sql)


def get_playlist_songs(playlist_id):
    sql = """
        SELECT songs.id, songs.title, artists.name AS artist,
               songs.duration_sec, playlist_songs.added_at
        FROM playlist_songs
        JOIN songs   ON songs.id   = playlist_songs.song_id
        JOIN albums  ON albums.id  = songs.album_id
        JOIN artists ON artists.id = albums.artist_id
        WHERE playlist_songs.playlist_id = ?
        ORDER BY playlist_songs.added_at, songs.title
    """
    return run_query(sql, (playlist_id,))


def create_playlist(user_id, name):
    sql = """
        INSERT INTO playlists (user_id, name)
        VALUES (?, ?)
    """
    return run_write(sql, (user_id, name))


def rename_playlist(playlist_id, name):
    sql = """
        UPDATE playlists
        SET name = ?
        WHERE id = ?
    """
    return run_write(sql, (name, playlist_id))


def delete_playlist(playlist_id):
    sql = """
        DELETE FROM playlists
        WHERE id = ?
    """
    return run_write(sql, (playlist_id,))


def add_song_to_playlist(playlist_id, song_id):
    sql = """
        INSERT INTO playlist_songs (playlist_id, song_id)
        VALUES (?, ?)
    """
    return run_write(sql, (playlist_id, song_id))


def remove_song_from_playlist(playlist_id, song_id):
    sql = """
        DELETE FROM playlist_songs
        WHERE playlist_id = ? AND song_id = ?
    """
    return run_write(sql, (playlist_id, song_id))


# =====================================================================
# USERS
# =====================================================================

def list_users():
    sql = """
        SELECT id, username, country, joined_date
        FROM users
        ORDER BY username
    """
    return run_query(sql)


def get_inactive_users():
    sql = """
        SELECT users.id, users.username, users.country, users.joined_date
        FROM users
        LEFT JOIN plays ON plays.user_id = users.id
        WHERE plays.id IS NULL
        ORDER BY users.username
    """
    return run_query(sql)


# =====================================================================
# CHARTS
# =====================================================================

def get_top_songs(limit):
    sql = """
        SELECT songs.id, songs.title, artists.name AS artist, COUNT(plays.id) AS play_count
        FROM plays
        JOIN songs   ON songs.id   = plays.song_id
        JOIN albums  ON albums.id  = songs.album_id
        JOIN artists ON artists.id = albums.artist_id
        GROUP BY songs.id
        ORDER BY play_count DESC, songs.title
        LIMIT ?
    """
    return run_query(sql, (limit,))


def get_genre_stats():
    sql = """
        SELECT genre,
               COUNT(*) AS song_count,
               ROUND(AVG(duration_sec), 1) AS avg_duration
        FROM songs
        GROUP BY genre
        ORDER BY song_count DESC, genre
    """
    return run_query(sql)


def get_prolific_artists(min_songs):
    sql = """
        SELECT artists.id, artists.name AS artist, COUNT(songs.id) AS song_count
        FROM artists
        JOIN albums ON albums.artist_id = artists.id
        JOIN songs  ON songs.album_id   = albums.id
        GROUP BY artists.id
        HAVING COUNT(songs.id) >= ?
        ORDER BY song_count DESC, artist
    """
    return run_query(sql, (min_songs,))


def get_genre_leaders():
    sql = """
        WITH song_plays AS (
            SELECT songs.genre, songs.title, COUNT(plays.id) AS play_count
            FROM songs
            JOIN plays ON plays.song_id = songs.id
            GROUP BY songs.id
        ),
        ranked AS (
            SELECT genre, title, play_count,
                   ROW_NUMBER() OVER (
                       PARTITION BY genre
                       ORDER BY play_count DESC, title
                   ) AS rank_in_genre
            FROM song_plays
        )
        SELECT genre, title, play_count
        FROM ranked
        WHERE rank_in_genre = 1
        ORDER BY genre
    """
    return run_query(sql)
