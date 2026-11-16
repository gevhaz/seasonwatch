"""Checking the stored series for new seasons."""

from datetime import date

from requests import Session

from seasonwatch.exceptions import SeasonwatchException
from seasonwatch.season_status import (
    CheckFailed,
    SeasonCheck,
    SeasonStatus,
    classify_season,
)
from seasonwatch.sql import Sql
from seasonwatch.tmdb import fetch_season


def check_for_new_seasons(session: Session, today: date) -> list[SeasonCheck]:
    """Return the status of the next season of every stored series.

    The next season is the one after the last season that the user has
    watched, and ``today`` is the day that its air date is compared to.

    A series that can't be looked up on TMDB gets the status
    ``CheckFailed`` and doesn't stop the remaining series from being
    checked.
    """
    season_checks: list[SeasonCheck] = []
    for series in Sql.read_all_series():
        next_season_number = int(series["last_season"]) + 1
        status: SeasonStatus
        try:
            next_season = fetch_season(session, series["id"], next_season_number)
        except SeasonwatchException as error:
            status = CheckFailed(reason=str(error))
        else:
            status = classify_season(next_season, today)
        season_checks.append(
            SeasonCheck(
                series_title=series["title"],
                season_number=next_season_number,
                status=status,
            )
        )
    return season_checks
