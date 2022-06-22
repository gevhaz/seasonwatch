#!/usr/bin/env python3

import imdb
import yaml
import notify2

from colorama import Fore, init
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
from dateutil.parser import ParserError
from imdb import Movie
from imdb.parser.http import IMDbHTTPAccessSystem
from imdb.parser.s3 import IMDbS3AccessSystem
from imdb.parser.sql import IMDbSqlAccessSystem
from pprint import PrettyPrinter
from typing import Any, Union

init(autoreset=True)

with open('series.yaml', 'r') as f:
    config: Any = yaml.safe_load(f)

ia: Union[IMDbHTTPAccessSystem, IMDbS3AccessSystem, IMDbSqlAccessSystem] = imdb.IMDb("https")
pp: PrettyPrinter = PrettyPrinter(indent=2)
notify2.init("seasonwatch")

for show_cfg in config['series']:
    current_season_cfg: int = show_cfg.get('current_season')
    title_cfg: str = show_cfg.get('title')
    id_cfg: str = show_cfg.get('id')
    if current_season_cfg is None or not title_cfg or not id_cfg:
        print("Data is missing from the config. Skipping this show")
        continue

    show_imdb = ia.get_movie(id_cfg, 'episodes')
    # ia.update(show_imdb, "episodes")
    episodes_imdb = show_imdb.data.get("episodes")

    if episodes_imdb:
        n_latest_season: int = max(episodes_imdb.keys())
    else:
        print(f"Couldn't load episodes for {title_cfg}. Skipping...")
        continue

    # There is a new season mentioned on IMDb
    if n_latest_season > current_season_cfg:

        next_season = current_season_cfg + 1
        release_dates_raw = ia.get_movie_release_dates(episodes_imdb[next_season][1].getID())

        # There is data about the release date for the new season
        release_data_imdb = release_dates_raw.get('data')
        if release_data_imdb:
            # Parse date from release dates of all countries and take the minimum
            raw_release_dates_imdb = release_data_imdb.get('raw release dates')
            if raw_release_dates_imdb:
                try:
                    earliest_date: datetime = min(parse(d['date'], default=datetime(2022, 12, 31)) for d in raw_release_dates_imdb)
                except ParserError as e:
                    print(Fore.RED + f"There was an error parsing a date value for the show {title_cfg}")
                    print(e)
                    continue
            else:
                continue

            # The new season is out
            if (earliest_date < datetime.now()):
                print(Fore.BLUE + f"Season {next_season} of {title_cfg} is out already!")
                n = notify2.Notification(title_cfg, f"Season {next_season} of {title_cfg} is out already!")
                n.show()
            # The new season is not yet out
            elif (earliest_date < datetime.now() + timedelta(days=90)):
                print(Fore.GREEN + f"Season {next_season} of {title_cfg} is not yet out but will "
                      f"be released on {earliest_date.strftime('%B %-d, %Y')}.")
                n = notify2.Notification(title_cfg,
                        f"Season {next_season} of {title_cfg} is not yet out but will "
                        f"be released on {earliest_date.strftime('%B %-d, %Y')}.")
                n.show()
            else:
                print(f"Season {next_season} of {title_cfg} coming up, in more than three months")
        # There is no data about the release date of the new season
        else:
            print(f"Season {next_season} of {title_cfg} is announced but "
                   "the release date is not yet determined")

    # There is no new season mentioned on IMDb
    else:
        print(f"No new season found for {title_cfg}")


exit()
