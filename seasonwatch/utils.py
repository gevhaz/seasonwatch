from datetime import date, datetime

from dateutil.parser import ParserError, parse
from imdb.parser.http import IMDbHTTPAccessSystem

from seasonwatch.exceptions import SeasonwatchException


class Utils:
    """
    Collection of utilities functions that are generally useful
    """

    @staticmethod
    def get_next_release_date(
        title: str,
        next_season: int,
        next_episode_id: str,
        ia: IMDbHTTPAccessSystem,
    ) -> datetime:
        imdb_release_data = ia.get_movie_release_dates(next_episode_id).get("data")

        # There is no data about the release date of the new season
        if imdb_release_data is None:
            print(
                f"Season {next_season} of {title} is announced but "
                "the release date is not yet determined"
            )

        # Parse date from release dates of all countries and take the minimum
        imdb_raw_release_dates = imdb_release_data.get("raw release dates")
        if imdb_raw_release_dates is None:
            raise SeasonwatchException(f"Couldn't find IMDb release dates for {title}")

        try:
            next_season_earliest_release: datetime = min(
                parse(d["date"], default=datetime(2022, 12, 31))
                for d in imdb_raw_release_dates
            )
        except ParserError as e:
            raise Exception(
                f"There was an error parsing date value for the show {title}: {e}"
            )

        return next_season_earliest_release

    @staticmethod
    def get_next_episode_id(
        id: str,
        last_watched_season: int,
        ia: IMDbHTTPAccessSystem,
    ) -> str | None:
        next_season = last_watched_season + 1

        imdb_all_seasons_data = ia.get_movie(id, "episodes").data.get("episodes")

        if imdb_all_seasons_data is None:
            raise SeasonwatchException("Couldn't load episodes. Skipping...")

        latest_available_season: int = max(imdb_all_seasons_data.keys())

        if latest_available_season <= last_watched_season:
            return None

        try:
            next_episode_id = str(imdb_all_seasons_data[next_season][1].getID())
        except ParserError:
            return None

        return next_episode_id

    @staticmethod
    def timestamp() -> str:
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    @staticmethod
    def sql_today() -> str:
        return date.today().strftime("%Y-%m-%d 00:00:00")

    @staticmethod
    def sql_date_to_python_date(sql_date: str) -> datetime:
        try:
            python_date = datetime.strptime(sql_date, "%Y-%m-%d 00:00:00")
        except ValueError:
            raise SeasonwatchException(f"Couldn't parse '{sql_date}' as date.")
        return python_date
