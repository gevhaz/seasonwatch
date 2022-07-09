import logging
import os
import sys

import gi

gi.require_version("Notify", "0.7")

from colorama import Fore, init
from gi.repository import Notify
from imdb import Cinemagoer
from imdb.parser.http import IMDbHTTPAccessSystem

from seasonwatch.config import ConfigParser
from seasonwatch.constants import Constants
from seasonwatch.exceptions import ConfigException, SeasonwatchException
from seasonwatch.media_watcher import MediaWatcher
from seasonwatch.sql import Sql

init(autoreset=True)


def main() -> int:

    config = ConfigParser()
    try:
        config.parse_config("series.yaml")
    except ConfigException as e:
        logging.error(f"Failed to parse config: {e}")

    Notify.init("Seasonwatch")
    ia: IMDbHTTPAccessSystem = Cinemagoer(accessSystem="https")
    watcher = MediaWatcher()

    if not Constants.DATA_DIRECTORY.exists():
        os.mkdir(Constants.DATA_DIRECTORY)

    Sql.ensure_table()

    if len(config.series) > 0:
        for show_cfg in config.series:
            try:
                watcher.check_for_new_seasons(show_cfg, ia)
            except SeasonwatchException as e:
                logging.error(f"Seasonwatch encountered an error: {e}")
                return 1

        for title, message in watcher.series["new"].items():
            print(Fore.BLUE + message)
            notification = Notify.Notification.new(title, message)
            notification.show()

        for title, message in watcher.series["soon"].items():
            print(Fore.GREEN + message)
            notification = Notify.Notification.new(title, message)
            notification.show()

        for title, message in watcher.series["later"].items():
            print(message)

        for title, message in watcher.series["nothing"].items():
            print(message)

    return 0


if __name__ == "__main__":
    sys.exit(main())
