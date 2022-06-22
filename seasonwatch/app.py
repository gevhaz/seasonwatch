import sys

import imdb
import yaml
import notify2

from colorama import Fore, init
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
from dateutil.parser import ParserError
from imdb.parser.http import IMDbHTTPAccessSystem
from imdb.parser.s3 import IMDbS3AccessSystem
from imdb.parser.sql import IMDbSqlAccessSystem
from typing import Any, Union

init(autoreset=True)


def main():

    with open('series.yaml', 'r') as f:
        config: Any = yaml.safe_load(f)

    ia: Union[IMDbHTTPAccessSystem, IMDbS3AccessSystem, IMDbSqlAccessSystem] = imdb.IMDb("https")
    notify2.init("seasonwatch")

    for show_cfg in config['series']:
        last_watched_season: int = show_cfg.get('current_season')
        series_name: str = show_cfg.get('title')
        series_id: str = show_cfg.get('id')

        if last_watched_season is None or series_name is None or series_id is None:
            print("Data is missing from the config. Skipping this show")
            continue

        imdb_all_seasons_data = ia.get_movie(series_id, 'episodes').data.get("episodes")

        if imdb_all_seasons_data is None:
            print(f"Couldn't load episodes for {series_name}. Skipping...")
            continue

        latest_available_season: int = max(imdb_all_seasons_data.keys())

        if latest_available_season <= last_watched_season:
            print(f"No new season found for {series_name}")
            continue

        next_unwatched_season = last_watched_season + 1
        imdb_release_data = ia.get_movie_release_dates(imdb_all_seasons_data[next_unwatched_season][1].getID()).get("data")

        # There is no data about the release date of the new season
        if imdb_release_data is None:
            print(f"Season {next_unwatched_season} of {series_name} is announced but "
                  "the release date is not yet determined")

        # Parse date from release dates of all countries and take the minimum
        imdb_raw_release_dates = imdb_release_data.get('raw release dates')
        if imdb_raw_release_dates is None:
            continue

        try:
            next_season_earliest_release: datetime = min(parse(d['date'], default=datetime(2022, 12, 31)) for d in imdb_raw_release_dates)
        except ParserError as e:
            print(Fore.RED + f"There was an error parsing a date value for the show {series_name}")
            print(e)
            continue

        # The new season is out
        if (next_season_earliest_release < datetime.now()):
            print(Fore.BLUE + f"Season {next_unwatched_season} of {series_name} is out already!")
            n = notify2.Notification(series_name, f"Season {next_unwatched_season} of {series_name} is out already!")
            n.show()
        # The new season is not yet out
        elif (next_season_earliest_release < datetime.now() + timedelta(days=90)):
            print(Fore.GREEN + f"Season {next_unwatched_season} of {series_name} is not yet out but will "
                  f"be released on {next_season_earliest_release.strftime('%B %-d, %Y')}.")
            n = notify2.Notification(series_name,
                    f"Season {next_unwatched_season} of {series_name} is not yet out but will "
                    f"be released on {next_season_earliest_release.strftime('%B %-d, %Y')}.")
            n.show()
        else:
            print(f"Season {next_unwatched_season} of {series_name} coming up, in more than three months")


if __name__ == "__main__":
    sys.exit(main())
