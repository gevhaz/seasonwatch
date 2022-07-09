import apsw

from seasonwatch.constants import Constants


class Sql:
    @staticmethod
    def ensure_table() -> None:
        connection = apsw.Connection(Constants.DATABASE_PATH)
        cursor = connection.cursor()

        cursor.execute("BEGIN TRANSACTION")
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {Constants.MOVIES_TABLE} (
                id INTEGER NOT NULL PRIMARY KEY,
                title TEXT NOT NULL,
                number_of_checks INGEGER DEFAULT 0,
                last_notified_date TEXT,
                last_change_date TEXT
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
                last_notified_date TEXT,
                last_change_date TEXT
            );
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
