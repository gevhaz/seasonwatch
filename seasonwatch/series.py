"""The TV shows that the user follows."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Series:
    """A TV show and how far the user has watched it."""

    # The number after "tv/" in the URL of the show on TMDB.
    tmdb_id: int
    # What the user calls the show, which needn't be its name on TMDB.
    title: str
    last_watched_season: int
