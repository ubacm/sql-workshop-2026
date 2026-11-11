"""
Builds data/tunes.db from schema.sql and fills it with fake (but realistic) data.

Run it any time to reset the database:
    python seed.py

The random generator uses a fixed seed, so everyone in the workshop
gets exactly the same data.
"""

import random
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
DB_PATH = PROJECT_DIR / "data" / "tunes.db"
SCHEMA_PATH = PROJECT_DIR / "schema.sql"

GENRES = ["Pop", "Rock", "Hip-Hop", "R&B", "Electronic", "Jazz", "Latin", "Indie", "Country"]
COUNTRIES = ["USA", "UK", "Canada", "Mexico", "Brazil", "Japan", "South Korea", "Nigeria", "Germany", "Colombia"]

ARTIST_NAMES = [
    "The Midnight Owls", "Luna Vega", "Static Bloom", "DJ Kilowatt", "Rosa Marquez",
    "Northbound", "Kai Tanaka", "The Paper Kites Club", "Velvet Signal", "Amara Obi",
    "Glass Harbor", "Lil Quasar", "Neon Cathedral", "Sofia Reyes Trio", "Blue Static",
    "Mason Creek", "Echo Park Kids", "Yuna Seo", "Cosmic Taco", "The Late Bloomers",
    "Marlow", "Iron & Honey", "Digital Daydream", "Papi Sol", "Hollow Pines",
]

# Song titles are built from these words, e.g. "Golden Midnight", "Electric Hearts"
TITLE_WORDS_A = ["Golden", "Electric", "Broken", "Midnight", "Neon", "Silver", "Wild", "Lonely",
                 "Summer", "Velvet", "Crystal", "Burning", "Hidden", "Paper", "Purple", "Cold"]
TITLE_WORDS_B = ["Hearts", "Skies", "Dreams", "Roads", "Lights", "Fire", "Rain", "Waves",
                 "City", "Echoes", "Shadows", "Ocean", "Heartbeat", "Love", "Static", "Stars"]

ALBUM_WORDS = ["Chapter", "Season", "Signals", "Origins", "Afterglow", "Horizons",
               "Daydreams", "Gravity", "Polaroids", "Tides", "Frequencies", "Mirrors"]

USERNAME_PARTS_A = ["beat", "sonic", "lofi", "vinyl", "bass", "melody", "tempo", "groove", "riff", "chill"]
USERNAME_PARTS_B = ["fan", "kid", "head", "lover", "nerd", "queen", "king", "wizard", "bull", "cat"]


def random_song_title(rng):
    title = f"{rng.choice(TITLE_WORDS_A)} {rng.choice(TITLE_WORDS_B)}"
    # A few songs get a suffix so the LIKE / search exercise is more interesting
    roll = rng.random()
    if roll < 0.07:
        title += " (Remix)"
    elif roll < 0.11:
        title += " (Acoustic)"
    elif roll < 0.14:
        title += " (Live)"
    return title


def build_database():
    rng = random.Random(42)

    DB_PATH.parent.mkdir(exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    connection = sqlite3.connect(DB_PATH)
    connection.executescript(SCHEMA_PATH.read_text())

    # ---- artists -------------------------------------------------------
    artist_genre = {}  # each artist mostly makes one genre
    for artist_id, name in enumerate(ARTIST_NAMES, start=1):
        connection.execute(
            "INSERT INTO artists (id, name, country, formed_year) VALUES (?, ?, ?, ?)",
            (artist_id, name, rng.choice(COUNTRIES), rng.randint(1995, 2021)),
        )
        artist_genre[artist_id] = rng.choice(GENRES)

    # ---- albums & songs ------------------------------------------------
    album_id = 0
    song_id = 0
    for artist_id in artist_genre:
        album_count = rng.choice([1, 1, 2, 2, 3, 4])
        for album_number in range(1, album_count + 1):
            album_id += 1
            album_title = f"{rng.choice(ALBUM_WORDS)} {album_number}" if rng.random() < 0.4 \
                else f"{rng.choice(TITLE_WORDS_A)} {rng.choice(ALBUM_WORDS)}"
            connection.execute(
                "INSERT INTO albums (id, artist_id, title, release_year) VALUES (?, ?, ?, ?)",
                (album_id, artist_id, album_title, rng.randint(2005, 2026)),
            )

            used_titles = set()
            for _ in range(rng.randint(4, 11)):
                title = random_song_title(rng)
                while title in used_titles:
                    title = random_song_title(rng)
                used_titles.add(title)

                # 80% of the time the song is the artist's main genre
                genre = artist_genre[artist_id] if rng.random() < 0.8 else rng.choice(GENRES)
                song_id += 1
                connection.execute(
                    "INSERT INTO songs (id, album_id, title, genre, duration_sec) VALUES (?, ?, ?, ?, ?)",
                    (song_id, album_id, title, genre, rng.randint(125, 330)),
                )
    total_songs = song_id

    # ---- users ---------------------------------------------------------
    usernames = set()
    total_users = 60
    for user_id in range(1, total_users + 1):
        username = f"{rng.choice(USERNAME_PARTS_A)}_{rng.choice(USERNAME_PARTS_B)}{rng.randint(1, 99)}"
        while username in usernames:
            username = f"{rng.choice(USERNAME_PARTS_A)}_{rng.choice(USERNAME_PARTS_B)}{rng.randint(1, 99)}"
        usernames.add(username)
        joined = date(2022, 1, 1) + timedelta(days=rng.randint(0, 1400))
        connection.execute(
            "INSERT INTO users (id, username, country, joined_date) VALUES (?, ?, ?, ?)",
            (user_id, username, rng.choice(COUNTRIES), joined.isoformat()),
        )

    # ---- plays ---------------------------------------------------------
    # Some songs are "hits" and get played a lot more than others.
    song_weights = [rng.paretovariate(1.3) for _ in range(total_songs)]
    inactive_users = set(rng.sample(range(1, total_users + 1), 7))  # never played anything
    play_id = 0
    start = datetime(2025, 1, 1)
    for user_id in range(1, total_users + 1):
        if user_id in inactive_users:
            continue
        for _ in range(rng.randint(10, 120)):
            play_id += 1
            chosen_song = rng.choices(range(1, total_songs + 1), weights=song_weights)[0]
            played_at = start + timedelta(minutes=rng.randint(0, 60 * 24 * 670))
            connection.execute(
                "INSERT INTO plays (id, user_id, song_id, played_at) VALUES (?, ?, ?, ?)",
                (play_id, user_id, chosen_song, played_at.strftime("%Y-%m-%d %H:%M:%S")),
            )

    # ---- playlists -----------------------------------------------------
    playlist_names = ["Gym Mix", "Study Session", "Road Trip", "Late Night", "Sunday Morning",
                      "Party Starters", "Rainy Day", "Throwbacks", "Focus Mode", "Good Vibes"]
    playlist_id = 0
    for user_id in rng.sample(range(1, total_users + 1), 25):
        for name in rng.sample(playlist_names, rng.randint(1, 2)):
            playlist_id += 1
            created = datetime(2025, 1, 1) + timedelta(days=rng.randint(0, 600))
            connection.execute(
                "INSERT INTO playlists (id, user_id, name, created_at) VALUES (?, ?, ?, ?)",
                (playlist_id, user_id, name, created.strftime("%Y-%m-%d %H:%M:%S")),
            )
            for song in rng.sample(range(1, total_songs + 1), rng.randint(5, 15)):
                added = created + timedelta(days=rng.randint(0, 60))
                connection.execute(
                    "INSERT INTO playlist_songs (playlist_id, song_id, added_at) VALUES (?, ?, ?)",
                    (playlist_id, song, added.strftime("%Y-%m-%d %H:%M:%S")),
                )

    connection.commit()
    connection.close()


if __name__ == "__main__":
    build_database()
    print(f"Database created at {DB_PATH}")
