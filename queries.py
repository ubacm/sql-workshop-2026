"""
=====================================================================
  queries.py — the data layer of Tunes. YOU write the SQL here.
=====================================================================

The app is already built: the frontend calls the API routes in app.py,
and each route calls one function in this file. Right now most of them
say  -- TODO, so those parts of the app show "Not implemented".
Write the SQL, save, refresh the page, and that feature comes to life.

Rules of the road
-----------------
* Use ? placeholders for values, never f-strings (that's how SQL injection happens).
  The params tuple is already written under each query: your ?'s must
  match its order.
* Return exactly the columns listed in the docstring (use AS to rename).
  The frontend reads those names, and so does the test suite.
* Test everything from the terminal:   python check_all.py

Suggested build order (★ easy  ★★ medium  ★★★ hard)
------------------------------------------------
  Artists page:    list_artists ★, get_artist ★, create_artist ★, update_artist ★,
                   delete_artist ★, get_artist_songs ★★
  Songs page:      list_genres ★, list_songs ★★, get_songs_by_genre ★★, search_songs ★★,
                   create_song ★, update_song ★, delete_song ★, record_play ★
  Users page:      list_users ★, get_inactive_users ★★★
  Playlists page:  get_playlist_songs ★★, create_playlist ★, rename_playlist ★,
                   delete_playlist ★, add_song_to_playlist ★, remove_song_from_playlist ★,
                   list_playlists ★★★
  Charts page:     get_genre_stats ★★, get_top_songs ★★★, get_prolific_artists ★★★,
                   get_genre_leaders (bonus)
"""

from db import run_query, run_query_one, run_write


# =====================================================================
# ARTISTS    (Artists page)
# =====================================================================

def list_artists():
    """
    ★ Every artist.  GET /api/artists

    Columns: id, name, country, formed_year
    Order:   by name, A to Z
    """
    sql = """
        -- TODO
    """
    return run_query(sql)


def get_artist(artist_id):
    """
    ★ One artist by id (the header of an artist's page).  GET /api/artists/<id>

    Columns: id, name, country, formed_year
    (run_query_one returns the first row, or None if there's no match.)
    """
    sql = """
        -- TODO
    """
    return run_query_one(sql, (artist_id,))


def get_artist_songs(artist_id):
    """
    ★★ Every song by one artist.  GET /api/artists/<id>/songs
    Hint: songs don't have an artist_id... but albums do.

    Columns: id, title, album, genre, duration_sec   (album = the album's title)
    Order:   by album, then by title
    """
    sql = """
        -- TODO
    """
    return run_query(sql, (artist_id,))


def create_artist(name, country, formed_year):
    """
    ★ "New artist" form.  POST /api/artists
    The id fills itself in.
    """
    sql = """
        -- TODO
    """
    return run_write(sql, (name, country, formed_year))


def update_artist(artist_id, name, country, formed_year):
    """
    ★ "Edit artist" form.  PUT /api/artists/<id>
    Careful: look at the ORDER of the params tuple. And don't forget WHERE!
    """
    sql = """
        -- TODO
    """
    return run_write(sql, (name, country, formed_year, artist_id))


def delete_artist(artist_id):
    """
    ★ Delete button on an artist's page.  DELETE /api/artists/<id>
    Try deleting an artist who has albums, then one you just created.
    Why does one fail? (Look at the albums table in schema.sql.)
    """
    sql = """
        -- TODO
    """
    return run_write(sql, (artist_id,))


# =====================================================================
# ALBUMS
# =====================================================================

def list_albums():
    """
    EXAMPLE, already written for you. Used by the album dropdown in the "New song" form.
    GET /api/albums

    Columns: id, title, release_year, artist
    Order:   by artist name, then release year

    Notice the pattern: JOIN on the foreign key (albums.artist_id = artists.id),
    and rename columns with AS so the frontend gets nice names.
    """
    sql = """
        SELECT albums.id, albums.title, albums.release_year, artists.name AS artist
        FROM albums
        JOIN artists ON artists.id = albums.artist_id
        ORDER BY artists.name, albums.release_year
    """
    return run_query(sql)


# =====================================================================
# SONGS    (Songs page)
# =====================================================================

def list_songs():
    """
    ★★ The main song library.  GET /api/songs
    You'll need two JOINs: songs → albums → artists.

    Columns: id, title, genre, duration_sec, album, artist
    Order:   by artist, then by title
    """
    sql = """
        -- TODO
    """
    return run_query(sql)


def list_genres():
    """
    ★ Every genre, each listed once (fills the genre filter dropdown).  GET /api/genres

    Columns: genre
    Order:   A to Z
    """
    sql = """
        -- TODO
    """
    return run_query(sql)


def get_songs_by_genre(genre):
    """
    ★★ Library filtered by the genre dropdown.  GET /api/songs?genre=Rock

    Columns: id, title, genre, duration_sec, album, artist   (same as list_songs)
    Order:   by artist, then by title
    """
    sql = """
        -- TODO
    """
    return run_query(sql, (genre,))


def search_songs(term):
    """
    ★★ The search bar.  GET /api/songs?q=love
    Match songs whose TITLE or ARTIST NAME contains `term` anywhere.
    (That's why `term` appears twice in the params tuple.)

    Columns: id, title, genre, duration_sec, album, artist   (same as list_songs)
    Order:   by artist, then by title
    """
    sql = """
        -- TODO
    """
    return run_query(sql, (term, term))


def create_song(album_id, title, genre, duration_sec):
    """
    ★ "New song" form.  POST /api/songs
    """
    sql = """
        -- TODO
    """
    return run_write(sql, (album_id, title, genre, duration_sec))


def update_song(song_id, title, genre, duration_sec):
    """
    ★ "Edit song" form.  PUT /api/songs/<id>
    """
    sql = """
        -- TODO
    """
    return run_write(sql, (title, genre, duration_sec, song_id))


def delete_song(song_id):
    """
    ★ Delete button on a song.  DELETE /api/songs/<id>
    Its plays and playlist entries are removed automatically (ON DELETE CASCADE).
    """
    sql = """
        -- TODO
    """
    return run_write(sql, (song_id,))


def record_play(user_id, song_id):
    """
    ★ The ▶ button: log that the signed-in user played a song.  POST /api/songs/<id>/play
    played_at fills itself in. Press ▶ a bunch and watch the Charts page change!
    """
    sql = """
        -- TODO
    """
    return run_write(sql, (user_id, song_id))


# =====================================================================
# PLAYLISTS    (Playlists page)
# =====================================================================

def list_playlists():
    """
    ★★★ Every playlist with its owner's username and how many songs it has.  GET /api/playlists
    Empty playlists must still show up (with song_count 0). Which JOIN keeps unmatched rows?

    Columns: id, name, owner, song_count
    Order:   by name, then by id
    """
    sql = """
        -- TODO
    """
    return run_query(sql)


def get_playlist_songs(playlist_id):
    """
    ★★ The songs inside one playlist.  GET /api/playlists/<id>/songs
    playlist_songs is a junction table: it links playlists ↔ songs.

    Columns: id, title, artist, duration_sec, added_at   (id = the song's id)
    Order:   oldest added_at first, then by title
    """
    sql = """
        -- TODO
    """
    return run_query(sql, (playlist_id,))


def create_playlist(user_id, name):
    """
    ★ "New playlist" button (owned by the signed-in user).  POST /api/playlists
    """
    sql = """
        -- TODO
    """
    return run_write(sql, (user_id, name))


def rename_playlist(playlist_id, name):
    """
    ★ "Rename" button.  PATCH /api/playlists/<id>
    """
    sql = """
        -- TODO
    """
    return run_write(sql, (name, playlist_id))


def delete_playlist(playlist_id):
    """
    ★ "Delete" button.  DELETE /api/playlists/<id>
    Its rows in playlist_songs disappear too. Check schema.sql to see why.
    """
    sql = """
        -- TODO
    """
    return run_write(sql, (playlist_id,))


def add_song_to_playlist(playlist_id, song_id):
    """
    ★ The "+" button on a song.  POST /api/playlists/<id>/songs
    Try adding the same song twice and read the error. What's protecting you?
    """
    sql = """
        -- TODO
    """
    return run_write(sql, (playlist_id, song_id))


def remove_song_from_playlist(playlist_id, song_id):
    """
    ★ The "remove" button inside a playlist.  DELETE /api/playlists/<id>/songs/<song_id>
    Make sure you only remove it from THIS playlist.
    """
    sql = """
        -- TODO
    """
    return run_write(sql, (playlist_id, song_id))


# =====================================================================
# USERS    (Users page + the "signed in as" picker)
# =====================================================================

def list_users():
    """
    ★ Every user.  GET /api/users

    Columns: id, username, country, joined_date
    Order:   by username, A to Z
    """
    sql = """
        SELECT * FROM users
        ORDER BY users.username
    """
    return run_query(sql)


def get_inactive_users():
    """
    ★★★ Users who have NEVER played a song.  GET /api/users/inactive
    Hint: LEFT JOIN + IS NULL, or NOT IN (subquery).

    Columns: id, username, country, joined_date
    Order:   by username, A to Z
    """
    sql = """
        -- TODO
    """
    return run_query(sql)


# =====================================================================
# CHARTS    (Charts page)
# =====================================================================

def get_genre_stats():
    """
    ★★ One row per genre with its song count and average length.  GET /api/charts/genres

    Columns: genre, song_count, avg_duration   (round avg_duration to 1 decimal)
    Order:   most songs first, then genre A to Z
    """
    sql = """
        -- TODO
    """
    return run_query(sql)


def get_top_songs(limit):
    """
    ★★★ Top charts: the most-played songs (count rows in `plays`).  GET /api/charts/top-songs?limit=10
    GROUP BY songs.id, not the title (two songs can share a title!).

    Columns: id, title, artist, play_count   (id = the song's id)
    Order:   most plays first, then title A to Z
    """
    sql = """
        -- TODO
    """
    return run_query(sql, (limit,))


def get_prolific_artists(min_songs):
    """
    ★★★ Artists with at least `min_songs` songs.  GET /api/charts/prolific-artists?min_songs=20
    WHERE filters rows before grouping; HAVING filters groups after.

    Columns: id, artist, song_count   (id = the artist's id)
    Order:   most songs first, then artist A to Z
    """
    sql = """
        -- TODO
    """
    return run_query(sql, (min_songs,))


def get_genre_leaders():
    """
    BONUS: the #1 most-played song in each genre.  GET /api/charts/genre-leaders
    Try a CTE (WITH ...) plus ROW_NUMBER() OVER (PARTITION BY genre ORDER BY ...).

    Columns: genre, title, play_count
    Order:   by genre A to Z (if two songs tie on plays, the title that comes first wins)
    """
    sql = """
        -- TODO
    """
    return run_query(sql)
