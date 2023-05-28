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
        episode = ia.get_movie(next_episode_id)
        episode_air_date = episode.get("original air date")

        # There is no data about the release date of the new season
        if episode_air_date is None:
            print(
                f"Season {next_season} of {title} is announced but "
                "the release date is not yet determined"
            )

        if not isinstance(episode_air_date, str):
            raise SeasonwatchException("Something is wrong with the air date data")

        next_season_earliest_release: datetime = parse(
            episode_air_date,
            default=datetime(2022, 12, 31),
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
        """Get today's date in format used by SQLite."""
        return date.today().strftime("%Y-%m-%d 00:00:00")

    @staticmethod
    def sql_date_to_python_date(sql_date: str) -> datetime:
        try:
            python_date = datetime.strptime(sql_date, "%Y-%m-%d 00:00:00")
        except ValueError:
            raise SeasonwatchException(f"Couldn't parse '{sql_date}' as date.")
        return python_date
