import logging
import sys

import imdb
import notify2
from colorama import Fore, init
from imdb.parser.http import IMDbHTTPAccessSystem
from imdb.parser.s3 import IMDbS3AccessSystem
from imdb.parser.sql import IMDbSqlAccessSystem

from seasonwatch.config import ConfigParser
from seasonwatch.exceptions import ConfigException, SeasonwatchException
from seasonwatch.media_watcher import MediaWatcher

init(autoreset=True)


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
            try:
                color, message = MediaWatcher.check_for_new_seasons(show_cfg, ia)
            except SeasonwatchException as e:
                logging.error(f"Seasonwatch encountered an error: {e}")
                return 1

            print(color + message)
            n = notify2.Notification(show_cfg["title"], message)
            n.show()


if __name__ == "__main__":
    sys.exit(main())
