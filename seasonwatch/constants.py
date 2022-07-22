from pathlib import Path


class Constants:
    DATA_DIRECTORY = Path.home() / ".seasonwatch"
    DATABASE_FILE = "database.sqlite"
    DATABASE_PATH = str(DATA_DIRECTORY / DATABASE_FILE)

    SERIES_TABLE = "series"
    MUSIC_TABLE = "music"
    MOVIES_TABLE = "movies"
    ARTIST_TABLE = "artists"
