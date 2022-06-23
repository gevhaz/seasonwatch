import logging
import sys
from typing import TypeAlias

import gi

gi.require_version("Notify", "0.7")

import imdb
from colorama import init
from gi.repository import Notify
from imdb.parser.http import IMDbHTTPAccessSystem
from imdb.parser.s3 import IMDbS3AccessSystem
from imdb.parser.sql import IMDbSqlAccessSystem

from seasonwatch.config import ConfigParser
from seasonwatch.exceptions import ConfigException, SeasonwatchException
from seasonwatch.media_watcher import MediaWatcher

init(autoreset=True)

IMDbObject: TypeAlias = IMDbHTTPAccessSystem | IMDbS3AccessSystem | IMDbSqlAccessSystem


def main() -> int:

    config = ConfigParser()
    try:
        config.parse_config("series.yaml")
    except ConfigException as e:
        logging.error(f"Failed to parse config: {e}")

    Notify.init("Seasonwatch")
    ia: IMDbObject = imdb.IMDb("https")

    if len(config.series) > 0:
        for show_cfg in config.series:
            try:
                color, message = MediaWatcher.check_for_new_seasons(show_cfg, ia)
            except SeasonwatchException as e:
                logging.error(f"Seasonwatch encountered an error: {e}")
                return 1

            print(color + message)
            notification = Notify.Notification.new(show_cfg["title"], message)
            notification.show()

    return 0


if __name__ == "__main__":
    sys.exit(main())
