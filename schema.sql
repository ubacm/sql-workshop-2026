-- =============================================================
--  Tunes — a tiny music streaming app
--  This is the full database schema. Read it before you start!
-- =============================================================

-- A band or solo musician.
CREATE TABLE artists (
    id           INTEGER PRIMARY KEY,
    name         TEXT    NOT NULL,
    country      TEXT    NOT NULL,
    formed_year  INTEGER NOT NULL
);

-- An album belongs to exactly one artist.
-- Note: NO cascade here. The database refuses to delete an artist who still has albums.
CREATE TABLE albums (
    id            INTEGER PRIMARY KEY,
    artist_id     INTEGER NOT NULL REFERENCES artists(id),
    title         TEXT    NOT NULL,
    release_year  INTEGER NOT NULL
);

-- A song belongs to exactly one album (and, through the album, one artist).
CREATE TABLE songs (
    id            INTEGER PRIMARY KEY,
    album_id      INTEGER NOT NULL REFERENCES albums(id),
    title         TEXT    NOT NULL,
    genre         TEXT    NOT NULL,
    duration_sec  INTEGER NOT NULL
);

-- Someone with an account on Tunes.
CREATE TABLE users (
    id           INTEGER PRIMARY KEY,
    username     TEXT    NOT NULL UNIQUE,
    country      TEXT    NOT NULL,
    joined_date  TEXT    NOT NULL          -- 'YYYY-MM-DD'
);

-- One row every time a user plays a song.
-- Deleting a song also deletes its plays (ON DELETE CASCADE).
CREATE TABLE plays (
    id         INTEGER PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    song_id    INTEGER NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
    played_at  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP   -- 'YYYY-MM-DD HH:MM:SS'
);

-- A playlist is owned by one user.
CREATE TABLE playlists (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    name        TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Junction table: which songs are in which playlist (many-to-many).
-- Deleting a playlist OR a song automatically deletes its rows here (ON DELETE CASCADE).
CREATE TABLE playlist_songs (
    playlist_id  INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
    song_id      INTEGER NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
    added_at     TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (playlist_id, song_id)
);
