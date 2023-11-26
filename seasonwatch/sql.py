import os
import shutil
from pathlib import Path
from typing import Any

import apsw
from prettytable.prettytable import from_db_cursor

from seasonwatch.constants import Constants
from seasonwatch.exceptions import SeasonwatchException
from seasonwatch.utils import Utils

DATABASE_FILE = "database.sqlite"
DATABASE_PATH = str(Constants.DATA_DIRECTORY / DATABASE_FILE)


class Sql:
    @staticmethod
    def ensure_table() -> None:
        connection = apsw.Connection(DATABASE_PATH)
        cursor = connection.cursor()

        cursor.execute("BEGIN TRANSACTION")

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {Constants.MOVIES_TABLE} (
                id TEXT NOT NULL PRIMARY KEY UNIQUE,
                title TEXT NOT NULL,
                number_of_checks INGEGER DEFAULT 0,
                last_notified_date TEXT DEFAULT '1970-01-01 00:00:00',
                last_change_date TEXT DEFAULT '1970-01-01 00:00:00'
            );
            """
        )

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {Constants.SERIES_TABLE} (
                id TEXT NOT NULL PRIMARY KEY UNIQUE,
                title TEXT NOT NULL,
                last_watched_season INTEGER DEFAULT 0,
                number_of_checks INGEGER DEFAULT 0,
                last_notified_date TEXT DEFAULT '1970-01-01 00:00:00',
                last_change_date TEXT DEFAULT '1970-01-01 00:00:00'
            );
            """
        )
        cursor.execute("COMMIT TRANSACTION")
        connection.close()

    @staticmethod
    def backup_database() -> None:
        N_BACKUPS = 10
        if Path(DATABASE_PATH).exists():
            backup_path = Path(
                Constants.DATA_DIRECTORY / str(Utils.timestamp() + "_database.sqlite")
            )
            shutil.copyfile(DATABASE_PATH, backup_path)

        dir_content = os.listdir(Constants.DATA_DIRECTORY)
        dir_content.remove(Constants.DATABASE_FILE)
        dir_content.sort(reverse=True)
        files_to_remove = set(dir_content).difference(set(dir_content[0:N_BACKUPS]))
        for file in files_to_remove:
            if "database" in file:
                os.remove(Constants.DATA_DIRECTORY / file)

    @staticmethod
    def remove_series(id: str) -> None:
        """Remove the show with the specified ID from the database.

        Remove the show with the specified id from the database so that
        it will no longer be checked for new seasons or have any traces
        saved by seasonwatch.
        """
        connection = apsw.Connection(DATABASE_PATH)
        cursor = connection.cursor()

        cursor.execute("BEGIN TRANSACTION")
        cursor.execute(
            f"""
            DELETE FROM {Constants.SERIES_TABLE}
            WHERE id = {id};
            """
        )
        cursor.execute("COMMIT TRANSACTION")
        connection.close()

    @staticmethod
    def update_series(
        id: str,
        title: str,
        last: int,
        checks: int,
        last_change: str,
        last_notify: str,
    ) -> None:
        connection = apsw.Connection(DATABASE_PATH)
        cursor = connection.cursor()

        checks = checks + 1

        cursor.execute("BEGIN TRANSACTION")
        cursor.execute(
            f"""
            INSERT OR REPLACE INTO {Constants.SERIES_TABLE} (
                id,
                title,
                last_watched_season,
                number_of_checks,
                last_notified_date,
                last_change_date
            )
            VALUES({id}, '{title}', {last}, {checks}, '{last_notify}', '{last_change}');
            """
        )
        cursor.execute("COMMIT TRANSACTION")
        connection.close()

    @staticmethod
    def step_up_series(id: str) -> None:
        """Increase last_watched_season value by one for show with id.

        Step up the last watched season number for the show with the
        specified id in the database.
        """
        connection = apsw.Connection(DATABASE_PATH)
        cursor = connection.cursor()

        cursor.execute("BEGIN TRANSACTION")
        transaction = f"""
            UPDATE {Constants.SERIES_TABLE}
            SET last_watched_season = last_watched_season + 1,
                last_change_date = '{Utils.sql_today()}'
            WHERE id = {id};
            """
        cursor.execute(transaction)
        cursor.execute("COMMIT TRANSACTION")
        connection.close()

    @staticmethod
    def read_series(id: str) -> dict[str, str]:
        """
        Return data from the database for the season with id `id`
        """
        connection = apsw.Connection(DATABASE_PATH)
        cursor = connection.cursor()
        values: dict[str, str] = {}
        for _, title, last, check, notified, change in cursor.execute(
            f"""
            SELECT
                id,
                title,
                last_watched_season,
                number_of_checks,
                last_notified_date,
                last_change_date
            FROM
                {Constants.SERIES_TABLE}
            WHERE
                id = {id};
            """
        ):
            # Safe to assume only one show with a specific ID
            values = {
                "id": id,
                "title": title,
                "last_season": last,
                "last_check": check,
                "last_notified": notified,
                "last_changed": change,
            }
            # cursor.execute("COMMIT TRANSACTION")
        connection.close()
        return values

    @staticmethod
    def read_all_series() -> list[dict[str, str]]:
        """Return data from the database for every TV show registered.

        Read all data about TV shows in the database, including data
        about id, last watched season, number of checks, etc.
        """
        connection = apsw.Connection(DATABASE_PATH)
        cursor = connection.cursor()
        values: list[dict[str, str]] = []
        for id, title, last, check, notified, change in cursor.execute(
            f"""
            SELECT
                id,
                title,
                last_watched_season,
                number_of_checks,
                last_notified_date,
                last_change_date
            FROM
                {Constants.SERIES_TABLE}
            """
        ):
            # Safe to assume only one show with a specific ID
            values.append(
                {
                    "id": id,
                    "title": title,
                    "last_season": last,
                    "last_check": check,
                    "last_notified": notified,
                    "last_changed": change,
                }
            )
            # cursor.execute("COMMIT TRANSACTION")
        connection.close()
        return values

    @staticmethod
    def get_printable_series_table() -> Any:
        """Get a table with data about all saved TV shows.

        This function returns a PrettyTable object with the most
        user-relevant data selected from the database. No styling is
        performed on the table, except for naming the columns.

        :raises SeasonwatchException: If there is an issues with reading
            the data from the database.
        :return: The table with information about all saved series.
        """
        connection = apsw.Connection(DATABASE_PATH)
        cursor = connection.cursor()
        cursor.execute(
            f"""
            SELECT
                title,
                last_watched_season,
                'https://www.imdb.com/title/tt' || id
            FROM
                {Constants.SERIES_TABLE}
            """
        )
        table = from_db_cursor(cursor)  # type: ignore
        if table is None:
            raise SeasonwatchException("Couldn't create table from database cursor")

        table.field_names = [
            "Title",
            "Last watched season",
            "IMDb link",
        ]
        connection.close()
        return table
