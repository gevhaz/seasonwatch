"""What is known about the next season of a series."""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Final, NoReturn, Union

from seasonwatch.tmdb import Season

# A season counts as coming soon if it airs within this many days.
DAYS_COUNTED_AS_SOON: Final[int] = 90


@dataclass(frozen=True)
class Released:
    """The season has started airing."""

    air_date: date


@dataclass(frozen=True)
class ComingSoon:
    """The season starts airing within ``DAYS_COUNTED_AS_SOON`` days."""

    air_date: date


@dataclass(frozen=True)
class ComingLater:
    """The season starts airing, but not within what counts as soon."""

    air_date: date


@dataclass(frozen=True)
class Unscheduled:
    """TMDB lists the season, but without an air date."""


@dataclass(frozen=True)
class NotAnnounced:
    """TMDB doesn't list the season."""


SeasonStatus = Union[Released, ComingSoon, ComingLater, Unscheduled, NotAnnounced]


@dataclass(frozen=True)
class SeasonCheck:
    """The result of checking one series for its next season."""

    series_title: str
    season_number: int
    status: SeasonStatus


def classify_season(season: Season | None, today: date) -> SeasonStatus:
    """Return the status that a season has on the day ``today``.

    Pass None as the season if TMDB doesn't list it. A season that
    starts airing today counts as released.
    """
    if season is None:
        return NotAnnounced()
    if season.air_date is None:
        return Unscheduled()
    if season.air_date <= today:
        return Released(air_date=season.air_date)

    last_day_counted_as_soon = today + timedelta(days=DAYS_COUNTED_AS_SOON)
    if season.air_date <= last_day_counted_as_soon:
        return ComingSoon(air_date=season.air_date)
    return ComingLater(air_date=season.air_date)


def assert_never(value: NoReturn) -> NoReturn:
    """Fail type checking if a kind of ``SeasonStatus`` is left unhandled.

    Call it with the status after handling every kind with
    ``isinstance``. mypy then reports a kind that has no branch.
    """
    raise AssertionError(f"Unhandled value: {value!r}")
