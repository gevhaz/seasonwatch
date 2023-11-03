import os
from pathlib import Path


class Constants:
    DATA_DIRECTORY = Path(
        os.environ.get(
            "XDG_DATA_HOME",
            default=Path.home() / ".local" / "share" / "seasonwatch",
        )
    )
    CONFIG_DIRECTORY = Path(
        os.environ.get(
            "XDG_CONFIG_HOME",
            default=Path.home() / ".config",
        )
    )
    CONFIG_FILE = "seasonwatchrc"
    CONFIG_PATH = CONFIG_DIRECTORY / CONFIG_FILE
    DATABASE_FILE = "database.sqlite"
    DATABASE_PATH = str(DATA_DIRECTORY / DATABASE_FILE)

    SERIES_TABLE = "series"
    MOVIES_TABLE = "movies"
