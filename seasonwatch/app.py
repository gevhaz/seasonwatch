"""The entry point of the command-line application."""

import sys
from argparse import Namespace
from configparser import ConfigParser
from datetime import date

import apsw
from colorama import init

from seasonwatch import series_menu, sql
from seasonwatch.cli import parse_arguments
from seasonwatch.config import load_configuration, read_tmdb_token, store_tmdb_token
from seasonwatch.constants import Constants
from seasonwatch.exceptions import SeasonwatchException
from seasonwatch.media_watcher import check_for_new_seasons
from seasonwatch.presentation import format_series_table
from seasonwatch.report import report_season_checks
from seasonwatch.season_status import CheckFailed
from seasonwatch.tmdb import check_token, create_session

init(autoreset=True)


def configure_tmdb_token(configuration: ConfigParser) -> int:
    """Ask the user for a TMDB token, test it and store it.

    Returns the exit status.

    :raises SeasonwatchException: If the token doesn't work.
    """
    new_tmdb_token = input("TMDB API Read Access Token: ")
    print("Testing token...")
    check_token(new_tmdb_token)
    print("Token is valid!")

    overwrite_config = input("Write new config file, losing all comments? (Y/n): ")
    if overwrite_config == "n" or overwrite_config == "N":
        print(
            f"Please manually update '{Constants.CONFIG_PATH}' with 'tmdb_token' "
            "under [Tokens]"
        )
        return 0
    store_tmdb_token(configuration, new_tmdb_token)
    print("Successfully set TMDB token!")
    return 0


def manage_series(arguments: Namespace, connection: apsw.Connection) -> int:
    """Run the actions of the ``tv`` subcommand that the arguments ask for.

    Returns the exit status.

    :raises SeasonwatchException: If the user enters something that
        can't be used when adding a series.
    """
    if arguments.add:
        series_menu.add_series(connection)
    if arguments.remove:
        series_menu.remove_series(connection)
    if arguments.step_up:
        series_menu.step_up_series(connection)
    if arguments.list_shows:
        print(format_series_table(sql.read_all_series(connection)))
    return 0


def check_series(connection: apsw.Connection, tmdb_token: str) -> int:
    """Check all series for new seasons and tell the user the result.

    Returns the exit status, which is 1 if any series couldn't be checked.

    :raises SeasonwatchException: If TMDB can't be reached.
    """
    season_checks = check_for_new_seasons(
        connection,
        create_session(tmdb_token),
        today=date.today(),
    )

    report_season_checks(season_checks)

    for season_check in season_checks:
        if isinstance(season_check.status, CheckFailed):
            return 1
    return 0


def run_subcommand(arguments: Namespace) -> int:
    """Run the subcommand that the arguments ask for and return the exit status.

    :raises SeasonwatchException: If the subcommand can't be completed.
    """
    configuration = load_configuration()
    if arguments.subparser_name == "configure":
        return configure_tmdb_token(configuration)

    tmdb_token = read_tmdb_token(configuration)
    if tmdb_token is None:
        print("You need to set a TMDb token. Run 'seasonwatch configure'")
        return 1

    # The database is only touched by the subcommands that use it, and
    # only after the arguments are known to be valid.
    sql.backup_database(sql.DATABASE_PATH)
    connection = sql.open_database(sql.DATABASE_PATH)
    try:
        if arguments.subparser_name == "tv":
            return manage_series(arguments, connection)
        return check_series(connection, tmdb_token)
    finally:
        connection.close()


def main() -> int:
    """Run the application and return its exit status.

    This is the one place that turns an error into a message for the
    user and a failing exit status.
    """
    arguments = parse_arguments()
    try:
        return run_subcommand(arguments)
    except SeasonwatchException as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
