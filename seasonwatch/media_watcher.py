from datetime import datetime, timedelta
from typing import TypeAlias

from colorama import Fore
from imdb.parser.http import IMDbHTTPAccessSystem
from imdb.parser.s3 import IMDbS3AccessSystem
from imdb.parser.sql import IMDbSqlAccessSystem

from seasonwatch.exceptions import SeasonwatchException
from seasonwatch.utils import Utils

IMDbObject: TypeAlias = IMDbHTTPAccessSystem | IMDbS3AccessSystem | IMDbSqlAccessSystem


class MediaWatcher:
    """
    Class for checking for new media given a config
    """

    @staticmethod
    def check_for_new_seasons(
        series_config: dict[str, str],
        ia: IMDbObject,
    ) -> tuple[str, str]:
        last_watched_season = int(series_config["current_season"])
        next_season = last_watched_season + 1
        name = series_config["title"]
        id = series_config["id"]

        try:
            next_episode_id = Utils.get_next_episode_id(id, last_watched_season, ia)
        except SeasonwatchException as e:
            return Fore.RED, f"{name}: {str(e)}"

        if next_episode_id is None:
            return Fore.RESET, f"No new season found for {name}"

        try:
            next_season_earliest_release = Utils.get_next_release_date(
                name,
                next_season,
                next_episode_id,
                ia,
            )
        except SeasonwatchException as e:
            return Fore.RED, str(e)

        # The new season is out
        if next_season_earliest_release < datetime.now():
            message = f"Season {next_season} of {name} is out already!"
            return Fore.BLUE, message
        # The new season is not yet out
        elif next_season_earliest_release < datetime.now() + timedelta(days=90):
            message = (
                f"Season {next_season} of {name} is not yet out but "
                "will be released on "
                f"{next_season_earliest_release.strftime('%B %-d, %Y')}."
            )
            return Fore.GREEN, message
        else:
            message = (
                f"Season {next_season} of {name} coming up, in more "
                "than three months"
            )
            return Fore.RESET, message
