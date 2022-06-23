import logging
import sys
from datetime import datetime, timedelta

import imdb
import notify2
from colorama import Fore, init
from dateutil.parser import ParserError, parse
from imdb.parser.http import IMDbHTTPAccessSystem
from imdb.parser.s3 import IMDbS3AccessSystem
from imdb.parser.sql import IMDbSqlAccessSystem

from seasonwatch.config import ConfigParser
from seasonwatch.exceptions import ConfigException

init(autoreset=True)


def check_for_new_seasons(series_config: dict[str, str], ia) -> tuple[str, str]:
    last_watched_season: int = int(series_config["current_season"])
    series_name: str = series_config["title"]
    series_id: str = series_config["id"]

    imdb_all_seasons_data = ia.get_movie(series_id, "episodes").data.get("episodes")

    if imdb_all_seasons_data is None:
        return Fore.YELLOW, f"Couldn't load episodes for {series_name}. Skipping..."

    latest_available_season: int = max(imdb_all_seasons_data.keys())

    if latest_available_season <= last_watched_season:
        return Fore.RESET, f"No new season found for {series_name}"

    next_unwatched_season = last_watched_season + 1
    imdb_release_data = ia.get_movie_release_dates(
        imdb_all_seasons_data[next_unwatched_season][1].getID()
    ).get("data")

    # There is no data about the release date of the new season
    if imdb_release_data is None:
        print(
            f"Season {next_unwatched_season} of {series_name} is announced but "
            "the release date is not yet determined"
        )

    # Parse date from release dates of all countries and take the minimum
    imdb_raw_release_dates = imdb_release_data.get("raw release dates")
    if imdb_raw_release_dates is None:
        return Fore.YELLOW, f"Couldn't find IMDb release dates for {series_name}"

    try:
        next_season_earliest_release: datetime = min(
            parse(d["date"], default=datetime(2022, 12, 31))
            for d in imdb_raw_release_dates
        )
    except ParserError as e:
        raise Exception(
            f"There was an error parsing date value for the show {series_name}: {e}"
        )

    # The new season is out
    if next_season_earliest_release < datetime.now():
        message = f"Season {next_unwatched_season} of {series_name} is out already!"
        return Fore.BLUE, message
    # The new season is not yet out
    elif next_season_earliest_release < datetime.now() + timedelta(days=90):
        message = (
            f"Season {next_unwatched_season} of {series_name} is not yet out but "
            "will be released on "
            f"{next_season_earliest_release.strftime('%B %-d, %Y')}."
        )
        return Fore.GREEN, message
    else:
        message = (
            f"Season {next_unwatched_season} of {series_name} coming up, in more "
            "than three months"
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
