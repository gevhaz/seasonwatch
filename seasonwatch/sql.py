import os
import shutil
from pathlib import Path

import apsw

from seasonwatch.constants import Constants
from seasonwatch.utils import Utils


class Sql:
    @staticmethod
    def ensure_table() -> None:
        connection = apsw.Connection(Constants.DATABASE_PATH)
        cursor = connection.cursor()

        cursor.execute("BEGIN TRANSACTION")

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {Constants.MOVIES_TABLE} (
                id INTEGER NOT NULL PRIMARY KEY UNIQUE,
                title TEXT NOT NULL,
                number_of_checks INGEGER DEFAULT 0,
                last_notified_date TEXT DEFAULT '1970-01-01 00:00:00',
                last_change_date TEXT DEFAULT '1970-01-01 00:00:00'
            );
            """
        )

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {Constants.MUSIC_TABLE} (
                album_id INTEGER NOT NULL PRIMARY KEY UNIQUE,
                album_name TEXT NOT NULL,
                artist_id INTEGER NOT NULL,
                year INTEGER,
                n_notifications INGEGER DEFAULT 0,
                added_date TEXT NOT NULL,
                last_notified_date TEXT DEFAULT '1970-01-01 00:00:00'
            );
            """
        )

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {Constants.ARTIST_TABLE} (
                artist_id INTEGER NOT NULL PRIMARY KEY UNIQUE,
                artist_name TEXT NOT NULL,
                new TEXT NOT NULL
            );
            """
        )

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {Constants.SERIES_TABLE} (
                id INTEGER NOT NULL PRIMARY KEY UNIQUE,
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
        if Path(Constants.DATABASE_PATH).exists():
            backup_path = Path(
                Constants.DATA_DIRECTORY / str(Utils.timestamp() + "_database.sqlite")
            )
            shutil.copyfile(Constants.DATABASE_PATH, backup_path)

        dir_content = os.listdir(Constants.DATA_DIRECTORY)
        dir_content.remove(Constants.DATABASE_FILE)
        dir_content.sort(reverse=True)
        files_to_remove = set(dir_content).difference(set(dir_content[0:N_BACKUPS]))
        for file in files_to_remove:
            if "database" in file:
                os.remove(Constants.DATA_DIRECTORY / file)

    @staticmethod
    def update_series(
        id: str,
        title: str,
        last: int,
        checks: int,
        last_change: str,
        last_notify: str,
    ) -> None:
        connection = apsw.Connection(Constants.DATABASE_PATH)
        cursor = connection.cursor()
        # cursor.s
        # cursor.setrowtrace(rowtrace)

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
    def read_series(id: str) -> dict[str, str]:
        """
        Return data from the database for the season with id `id`
        """
        connection = apsw.Connection(Constants.DATABASE_PATH)
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
        """
        Return data from the database for every TV show registered.
        """
        connection = apsw.Connection(Constants.DATABASE_PATH)
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
    def update_music(
        album_id: str,
        album: str,
        artist_id: str,
        year: str,
        n_notifications: str,
        added_date: str,
        notified_date: str,
    ) -> None:
        connection = apsw.Connection(Constants.DATABASE_PATH)
        cursor = connection.cursor()

        album = album.replace("'", "''")
        if not year:
            year = "NULL"

        cursor.execute("BEGIN TRANSACTION")
        cursor.execute(
            f"""
            INSERT OR REPLACE INTO {Constants.MUSIC_TABLE} (
                album_id,
                album_name,
                artist_id,
                year,
                n_notifications,
                added_date,
                last_notified_date
            )
            VALUES(
                {album_id},
                '{album}',
                {artist_id},
                {year},
                {n_notifications},
                '{added_date}',
                '{notified_date}'
            );
            """
        )
        cursor.execute("COMMIT TRANSACTION")
        connection.close()

    @staticmethod
    def read_all_music() -> list[dict[str, str]]:
        """
        Return data from the database for every album registered.
        """
        connection = apsw.Connection(Constants.DATABASE_PATH)
        cursor = connection.cursor()
        values: list[dict[str, str]] = []
        for (
            album_id,
            album_name,
            artist_id,
            year,
            number_of_notifications,
            added_date,
            last_notified,
        ) in cursor.execute(
            f"""
            SELECT
                album_id,
                album_name,
                artist_id,
                year,
                n_notifications,
                added_date,
                last_notified_date
            FROM
                {Constants.MUSIC_TABLE}
            """
        ):
            # Safe to assume only one album with a specific ID
            values.append(
                {
                    "album_id": album_id,
                    "album_name": album_name,
                    "artist_id": artist_id,
                    "year": year,
                    "n_notifications": number_of_notifications,
                    "added_date": added_date,
                    "last_notified": last_notified,
                }
            )
            # cursor.execute("COMMIT TRANSACTION")
        connection.close()
        return values

    @staticmethod
    def add_artist(id: int, name: str) -> None:
        connection = apsw.Connection(Constants.DATABASE_PATH)
        cursor = connection.cursor()
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute(
            f"""
            INSERT OR REPLACE INTO {Constants.ARTIST_TABLE} (
                artist_id,
                artist_name,
                new
            )
            VALUES(
                {id},
                '{name}',
                'true'

            );
            """
        )
        cursor.execute("COMMIT TRANSACTION")
        connection.close()

    @staticmethod
    def unmark_artist_new(id: str, name: str) -> None:
        connection = apsw.Connection(Constants.DATABASE_PATH)
        cursor = connection.cursor()
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute(
            f"""
            INSERT OR REPLACE INTO {Constants.ARTIST_TABLE} (
                artist_id,
                artist_name,
                new
            )
            VALUES(
                {id},
                '{name}',
                'false'

            );
            """
        )
        cursor.execute("COMMIT TRANSACTION")
        connection.close()

    @staticmethod
    def read_all_artists() -> list[dict[str, str]]:
        """
        Return all registered artist IDs together with the artist name.
        """
        connection = apsw.Connection(Constants.DATABASE_PATH)
        cursor = connection.cursor()
        values: list[dict[str, str]] = []
        for id, artist, new in cursor.execute(
            f"""
            SELECT
                artist_id,
                artist_name,
                new
            FROM
                {Constants.ARTIST_TABLE}
            """
        ):
            # Safe to assume only one album with a specific ID
            values.append(
                {
                    "id": id,
                    "name": artist,
                    "new": new,
                }
            )
            # cursor.execute("COMMIT TRANSACTION")
        connection.close()
        return values
