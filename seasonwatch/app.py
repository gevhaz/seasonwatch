import logging
import os
import sys

import gi

from seasonwatch.cli import Cli

gi.require_version("Notify", "0.7")

from colorama import Fore, init
from gi.repository import Notify
from imdb import Cinemagoer
from imdb.parser.http import IMDbHTTPAccessSystem

from seasonwatch.config import Configure
from seasonwatch.constants import Constants
from seasonwatch.exceptions import SeasonwatchException
from seasonwatch.media_watcher import MediaWatcher
from seasonwatch.sql import Sql

init(autoreset=True)


def main() -> int:

    Sql.backup_database()
    Sql.ensure_table()

    args = Cli.parse()
    if args.subparser_name == "configure":
        if args.series:
            Configure.series()
        if args.artists:
            Configure.artists()
        return 0

    Notify.init("Seasonwatch")
    ia: IMDbHTTPAccessSystem = Cinemagoer(accessSystem="https")
    watcher = MediaWatcher()

    if not Constants.DATA_DIRECTORY.exists():
        os.mkdir(Constants.DATA_DIRECTORY)

    try:
        watcher.check_for_new_seasons(ia)
    except SeasonwatchException as e:
        logging.error(
            f"Seasonwatch encountered an error when checking for new seasons: {e}"
        )
        return 1

    try:
        watcher.check_for_new_music()
    except SeasonwatchException as e:
        logging.error(
            f"Seasonwatch encountered an error when checking for new music: {e}"
        )
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

    for album, message in watcher.music["new"].items():
        print(Fore.BLUE + message)
        notification = Notify.Notification.new(album, message)
        notification.show()

    for album, message in watcher.music["recent"].items():
        print(Fore.GREEN + message)

    return 0


if __name__ == "__main__":
    sys.exit(main())
