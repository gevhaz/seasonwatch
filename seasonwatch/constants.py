import os
from enum import Enum
from pathlib import Path
from typing import Final


class Constants:
    CONFIG_DIRECTORY: Final[Path] = Path(
        os.environ.get(
            "XDG_CONFIG_HOME",
            default=Path.home() / ".config",
        )
    )
    CONFIG_FILE: Final[str] = "seasonwatchrc"
    CONFIG_PATH: Final[Path] = CONFIG_DIRECTORY / CONFIG_FILE

    API_VERSION: Final[str] = "3"
    API_BASE_URL: Final[str] = f"https://api.themoviedb.org/{API_VERSION}"


class Source(Enum):
    """Enum with accepted TV Series information sources."""

    IMDB = "IMDb"
    TMDB = "TMDB"
