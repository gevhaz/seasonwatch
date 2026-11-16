"""Checking the stored series for new seasons."""

from datetime import date

import apsw
from requests import Session

from seasonwatch import sql
from seasonwatch.exceptions import TmdbResponseError
from seasonwatch.season_status import (
    CheckFailed,
    SeasonCheck,
    SeasonStatus,
    classify_season,
)
from seasonwatch.tmdb import fetch_season


def check_for_new_seasons(
    connection: apsw.Connection,
    session: Session,
    today: date,
) -> list[SeasonCheck]:
    """Return the status of the next season of every series in the database.

    The next season is the one after the last season that the user has
    watched, and ``today`` is the day that its air date is compared to.

    A series that TMDB responds with an error for gets the status
    ``CheckFailed`` and doesn't stop the remaining series from being
    checked.

    :raises SeasonwatchException: If TMDB can't be reached.
    """
    season_checks: list[SeasonCheck] = []
    for series in sql.read_all_series(connection):
        next_season_number = series.last_watched_season + 1
        status: SeasonStatus
        try:
            next_season = fetch_season(session, series.tmdb_id, next_season_number)
        except TmdbResponseError as error:
            status = CheckFailed(reason=str(error))
        else:
            status = classify_season(next_season, today)
        season_checks.append(
            SeasonCheck(
                series_title=series.title,
                season_number=next_season_number,
                status=status,
            )
        )
    return season_checks
