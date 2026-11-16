"""Access to the parts of the TMDB API that Seasonwatch needs."""

import sys
from dataclasses import dataclass
from datetime import date
from typing import Any

from requests import HTTPError, RequestException, Session

from seasonwatch.constants import Constants
from seasonwatch.exceptions import SeasonwatchException


@dataclass(frozen=True)
class Season:
    """One season of a TV show, with what TMDB knows about it."""

    number: int
    # None for as long as TMDB has no air date for the season.
    air_date: date | None


def parse_season(season_data: Any) -> Season:
    """Return the season described by one entry in TMDB's list of seasons.

    A missing or empty air date means that TMDB doesn't know it yet, and
    gives a season without an air date.

    :raises SeasonwatchException: If the entry has no season number, or
        an air date that isn't written as YYYY-MM-DD.
    """
    if not isinstance(season_data, dict):
        raise SeasonwatchException(f"Can't parse season from TMDB: {season_data}")

    season_number = season_data.get("season_number")
    if not isinstance(season_number, int):
        raise SeasonwatchException(
            f"Malformed season number returned from TMDB: {season_number}"
        )

    air_date_text = season_data.get("air_date")
    if air_date_text is None or air_date_text == "":
        return Season(number=season_number, air_date=None)
    if not isinstance(air_date_text, str):
        raise SeasonwatchException(
            f"Malformed air date returned from TMDB: {air_date_text}"
        )
    try:
        air_date = date.fromisoformat(air_date_text)
    except ValueError:
        raise SeasonwatchException(
            f"Malformed air date returned from TMDB: {air_date_text}"
        )
    return Season(number=season_number, air_date=air_date)


def find_season(series_data: Any, season_number: int) -> Season | None:
    """Return one season from TMDB's details of a series.

    Returns None if the series has no season with that number.

    :raises SeasonwatchException: If the details don't have the expected
        structure. Only the requested season is parsed, so malformed
        data for other seasons is not an error.
    """
    if not isinstance(series_data, dict):
        raise SeasonwatchException(f"Can't parse series from TMDB: {series_data}")
    all_seasons_data = series_data.get("seasons")
    if not isinstance(all_seasons_data, list):
        raise SeasonwatchException("No list of seasons in series data from TMDB.")

    for season_data in all_seasons_data:
        if not isinstance(season_data, dict):
            continue
        if season_data.get("season_number") == season_number:
            return parse_season(season_data)
    return None


def fetch_season(
    session: Session,
    series_id: str,
    season_number: int,
) -> Season | None:
    """Return one season of a series, or None if TMDB doesn't list it.

    Exits the application if TMDB can't be reached.

    :raises SeasonwatchException: If TMDB responds with an error or with
        data that can't be parsed.
    """
    url = f"{Constants.API_BASE_URL}/tv/{series_id}"
    try:
        response = session.get(url)
        response.raise_for_status()
        series_data = response.json()
    except HTTPError as e:
        raise SeasonwatchException(
            f"Failed connecting to TMDB for new seasons information: {e}"
        )
    except RequestException as e:
        print(f"There was an error fetching {url}: {e}")
        sys.exit(1)

    return find_season(series_data, season_number)
