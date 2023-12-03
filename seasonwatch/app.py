import logging
import sys
from configparser import ConfigParser

import gi
import requests
from prettytable.prettytable import SINGLE_BORDER
from requests import Session
from requests.exceptions import HTTPError

gi.require_version("Notify", "0.7")

from colorama import Fore, init
from gi.repository import Notify

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

    if not Constants.CONFIG_DIRECTORY.exists():
        Constants.CONFIG_DIRECTORY.mkdir(parents=True, exist_ok=True)
    if not (Constants.CONFIG_PATH).exists():
        (Constants.CONFIG_PATH).touch()

    args = Cli.parse()

    config = ConfigParser()
    config.read(Constants.CONFIG_PATH)
    if not config.has_section("Tokens"):
        config.add_section("Tokens")
        # Appending should preserve comments that the user has written.
        with open(Constants.CONFIG_PATH, mode="a") as fp:
            config.write(fp)

    tmdb_token: str | None = config.get("Tokens", "tmdb_token", fallback=None)
    if tmdb_token is None and args.subparser_name != "configure":
        print("You need to set a TMDb token. Run 'seasonwatch configure'")
        sys.exit(1)

    if args.subparser_name == "configure":
        new_tmdb_token = input("TMDB API Read Access Token: ")
        print("Testing token...")
        try:
            requests.get(
                f"{Constants.API_BASE_URL}/movie/11",
                headers={
                    "accept": "application/json",
                    "Authorization": f"Bearer {new_tmdb_token}",
                },
            ).raise_for_status()
        except HTTPError as e:
            if e.response is not None and e.response.status_code == 401:
                print("Invalid token. Please correct it.", file=sys.stderr)
            else:
                print(f"Error testing token: '{e}'", file=sys.stderr)
            sys.exit(1)
        print("Token is valid!")
        config.set(section="Tokens", option="tmdb_token", value=new_tmdb_token)
        overwrite_config = input("Write new config file, losing all comments? (Y/n): ")
        if overwrite_config == "n" or overwrite_config == "N":
            print(
                f"Please manually update '{Constants.CONFIG_PATH}' with 'tmdb_token' "
                "under [Tokens]"
            )
            sys.exit(0)
        with open(Constants.CONFIG_PATH, mode="w") as fp:
            config.write(fp)
        print("Successfully set TMDB token!")
        sys.exit(0)

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
    watcher = MediaWatcher()

    tmdb_session = Session()
    tmdb_session.headers.update(
        {
            "accept": "application/json",
            "Authorization": f"Bearer {tmdb_token}",
        }
    )

    try:
        watcher.check_for_new_seasons(session=tmdb_session)
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
