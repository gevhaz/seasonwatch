import logging
import sys
from configparser import ConfigParser

import gi
from prettytable.prettytable import SINGLE_BORDER

gi.require_version("Notify", "0.7")

from colorama import Fore, init
from gi.repository import Notify
from imdb import Cinemagoer
from imdb.parser.http import IMDbHTTPAccessSystem

from seasonwatch.cli import Cli
from seasonwatch.config import Configure
from seasonwatch.constants import Constants
from seasonwatch.exceptions import SeasonwatchException
from seasonwatch.media_watcher import MediaWatcher
from seasonwatch.sql import Sql

init(autoreset=True)


def main() -> int:
    Sql.backup_database()
    Sql.ensure_table()

    if not Constants.DATA_DIRECTORY.exists():
        Constants.DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)

    if not Constants.CONFIG_DIRECTORY.exists():
        Constants.CONFIG_DIRECTORY.mkdir(parents=True, exist_ok=True)
    if not (Constants.CONFIG_PATH).exists():
        (Constants.CONFIG_PATH).touch()

    args = Cli.parse()
    if args.subparser_name == "tv":
        if args.add:
            Configure.add_series()
        if args.remove:
            Configure.remove_series()
        if args.step_up:
            Configure.step_up_series()
        if args.list_shows:
            table = Sql.get_printable_series_table()
            table.set_style(SINGLE_BORDER)
            table.align = "l"
            print(table)
        return 0

    Notify.init("Seasonwatch")
    ia: IMDbHTTPAccessSystem = Cinemagoer(accessSystem="https")
    watcher = MediaWatcher()

    config = ConfigParser()
    config.read(Constants.CONFIG_PATH)

    try:
        watcher.check_for_new_seasons(ia)
    except SeasonwatchException as e:
        logging.error(
            f"Seasonwatch encountered an error when checking for new seasons: {e}"
        )
        return 1

    for title, message in watcher.series["new"].items():
        print(Fore.BLUE + message)
        notification = Notify.Notification.new(title, message)
        notification.set_timeout(10000)
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
