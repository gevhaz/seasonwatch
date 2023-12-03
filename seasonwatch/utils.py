from datetime import date, datetime
from typing import Any

from requests import HTTPError, Session

from seasonwatch.constants import Constants
from seasonwatch.exceptions import SeasonwatchException


class Utils:
    """
    Collection of utilities functions that are generally useful
    """

    @staticmethod
    def timestamp() -> str:
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    @staticmethod
    def sql_today() -> str:
        """Get today's date in format used by SQLite."""
        return date.today().strftime("%Y-%m-%d 00:00:00")

    @staticmethod
    def sql_date_to_python_date(sql_date: str) -> datetime:
        try:
            python_date = datetime.strptime(sql_date, "%Y-%m-%d 00:00:00")
        except ValueError:
            raise SeasonwatchException(f"Couldn't parse '{sql_date}' as date.")
        return python_date

    @staticmethod
    def get_next_season(
        id: str, current_season: int, session: Session
    ) -> dict[str, Any] | None:
        """Find the air date of the next season of a series."""
        url = f"{Constants.API_BASE_URL}/tv/{id}"
        try:
            response = session.get(url)
            response.raise_for_status()
            response_json = response.json()
        except HTTPError as e:
            raise SeasonwatchException(
                f"Failed connecting to TMDB for new seasons information: {e}"
            )

        seasons = response_json["seasons"]
        next_seasons = [s for s in seasons if s["season_number"] == current_season + 1]
        if not next_seasons:
            return None

        next_season = next_seasons[0]
        if not isinstance(next_season, dict):
            raise SeasonwatchException(f"Can't pase data from TMDB: {next_season}")

        return next_season
