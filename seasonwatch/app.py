import logging
import sys
from configparser import ConfigParser
from datetime import date

import requests
from colorama import init
from requests import RequestException, Session
from requests.exceptions import HTTPError

from seasonwatch import config, sql
from seasonwatch.cli import parse_arguments
from seasonwatch.constants import Constants
from seasonwatch.exceptions import SeasonwatchException
from seasonwatch.media_watcher import check_for_new_seasons
from seasonwatch.presentation import format_series_table
from seasonwatch.report import report_season_checks
from seasonwatch.season_status import CheckFailed

init(autoreset=True)


def main() -> int:
    sql.backup_database()
    try:
        sql.ensure_table()
    except SeasonwatchException as error:
        print(error, file=sys.stderr)
        return 1

    if not Constants.CONFIG_DIRECTORY.exists():
        Constants.CONFIG_DIRECTORY.mkdir(parents=True, exist_ok=True)
    if not (Constants.CONFIG_PATH).exists():
        (Constants.CONFIG_PATH).touch()

    args = parse_arguments()

    config_parser = ConfigParser()
    config_parser.read(Constants.CONFIG_PATH)
    if not config_parser.has_section("Tokens"):
        config_parser.add_section("Tokens")
        # Appending should preserve comments that the user has written.
        with open(Constants.CONFIG_PATH, mode="a") as fp:
            config_parser.write(fp)

    tmdb_token: str | None = config_parser.get("Tokens", "tmdb_token", fallback=None)
    if tmdb_token is None and args.subparser_name != "configure":
        print("You need to set a TMDb token. Run 'seasonwatch configure'")
        sys.exit(1)

    if args.subparser_name == "configure":
        new_tmdb_token = input("TMDB API Read Access Token: ")
        print("Testing token...")
        url = f"{Constants.API_BASE_URL}/movie/11"
        try:
            requests.get(
                url,
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
        except RequestException as e:
            print(f"There was an error fetching {url}: {e}")
            sys.exit(1)
        print("Token is valid!")
        config_parser.set(section="Tokens", option="tmdb_token", value=new_tmdb_token)
        overwrite_config = input("Write new config file, losing all comments? (Y/n): ")
        if overwrite_config == "n" or overwrite_config == "N":
            print(
                f"Please manually update '{Constants.CONFIG_PATH}' with 'tmdb_token' "
                "under [Tokens]"
            )
            sys.exit(0)
        with open(Constants.CONFIG_PATH, mode="w") as fp:
            config_parser.write(fp)
        print("Successfully set TMDB token!")
        sys.exit(0)

    if args.subparser_name == "tv":
        if args.add:
            config.add_series()
        if args.remove:
            config.remove_series()
        if args.step_up:
            config.step_up_series()
        if args.list_shows:
            print(format_series_table(sql.read_all_series()))
        return 0

    tmdb_session = Session()
    tmdb_session.headers.update(
        {
            "accept": "application/json",
            "Authorization": f"Bearer {tmdb_token}",
        }
    )

    try:
        season_checks = check_for_new_seasons(tmdb_session, today=date.today())
    except SeasonwatchException as e:
        logging.error(
            f"Seasonwatch encountered an error when checking for new seasons: {e}"
        )
        return 1

    report_season_checks(season_checks)

    for season_check in season_checks:
        if isinstance(season_check.status, CheckFailed):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
