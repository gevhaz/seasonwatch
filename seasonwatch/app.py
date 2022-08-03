import logging
import sys
from configparser import ConfigParser

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

    if not Constants.DATA_DIRECTORY.exists():
        Constants.DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)

    if not Constants.CONFIG_DIRECTORY.exists():
        Constants.CONFIG_DIRECTORY.mkdir(parents=True, exist_ok=True)
    if not (Constants.CONFIG_PATH).exists():
        (Constants.CONFIG_PATH).touch()

    args = Cli.parse()
    if args.subparser_name == "configure":
        if args.discogs_token:
            Configure.discogs_token()
        if args.series:
            Configure.series()
        if args.artists:
            Configure.artists()
        return 0

    Notify.init("Seasonwatch")
    ia: IMDbHTTPAccessSystem = Cinemagoer(accessSystem="https")
    watcher = MediaWatcher()

    config = ConfigParser()
    config.read(Constants.CONFIG_PATH)

    discogs_token = None
    if config.has_option("Tokens", "discogs_token"):
        discogs_token = config.get("Tokens", "discogs_token")
    try:
        watcher.check_for_new_music(discogs_token)
    except SeasonwatchException as e:
        logging.error(
            f"Seasonwatch encountered an error when checking for new music: {e}"
        )
        return 1

    for album, message in watcher.music["new"].items():
        print(Fore.BLUE + message)
        notification = Notify.Notification.new(album, message)
        notification.set_urgency(2)
        notification.show()

    for album, message in watcher.music["recent"].items():
        print(Fore.GREEN + message)
        notification = Notify.Notification.new(album, message)
        notification.set_timeout(12000)
        notification.show()

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
