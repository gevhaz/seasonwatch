import logging
import sys
from datetime import datetime, timedelta

import imdb
import notify2
from colorama import Fore, init
from imdb.parser.http import IMDbHTTPAccessSystem
from imdb.parser.s3 import IMDbS3AccessSystem
from imdb.parser.sql import IMDbSqlAccessSystem

from seasonwatch.config import ConfigParser
from seasonwatch.exceptions import ConfigException, SeasonwatchException
from seasonwatch.utils import Utils

init(autoreset=True)


def get_next_episode_id(id: str, last_watched_season: int, ia) -> str | None:
    next_season = last_watched_season + 1

    imdb_all_seasons_data = ia.get_movie(id, "episodes").data.get("episodes")

    if imdb_all_seasons_data is None:
        raise SeasonwatchException("Couldn't load episodes. Skipping...")

    latest_available_season: int = max(imdb_all_seasons_data.keys())

    if latest_available_season <= last_watched_season:
        return None

    return imdb_all_seasons_data[next_season][1].getID()


def check_for_new_seasons(series_config: dict[str, str], ia) -> tuple[str, str]:
    last_watched_season = int(series_config["current_season"])
    next_season = last_watched_season + 1
    name = series_config["title"]
    id = series_config["id"]

    try:
        next_episode_id = get_next_episode_id(id, last_watched_season, ia)
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
            f"Season {next_season} of {name} coming up, in more " "than three months"
        )
        return Fore.RESET, message


def main():

    config = ConfigParser()
    try:
        config.parse_config("series.yaml")
    except ConfigException as e:
        logging.error(f"Failed to parse config: {e}")

    notify2.init("seasonwatch")
    ia: IMDbHTTPAccessSystem | IMDbS3AccessSystem | IMDbSqlAccessSystem = imdb.IMDb(
        "https"
    )

    if len(config.series) > 0:
        for show_cfg in config.series:
            color, message = check_for_new_seasons(show_cfg, ia)
            print(color + message)
            n = notify2.Notification(show_cfg["title"], message)
            n.show()


if __name__ == "__main__":
    sys.exit(main())
