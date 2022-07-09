from pathlib import Path


class Constants:
    DATA_DIRECTORY = Path.home() / ".seasonwatch"
    DATABASE_PATH = str(DATA_DIRECTORY / "database.sqlite")

    SERIES_TABLE = "series"
    MOVIES_TABLE = "movies"
