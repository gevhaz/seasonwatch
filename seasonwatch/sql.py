import os
import shutil
from pathlib import Path
from typing import Any, Callable, Final, TypedDict

import apsw
from prettytable.prettytable import from_db_cursor

from seasonwatch.exceptions import SeasonwatchException
from seasonwatch.utils import Utils

DATA_DIRECTORY: Final[Path] = Path(
    os.environ.get(
        "XDG_DATA_HOME",
        default=Path.home() / ".local" / "share" / "seasonwatch",
    )
)
DATABASE_FILE: Final[str] = "database.sqlite"
DATABASE_PATH: Final[str] = str(DATA_DIRECTORY / DATABASE_FILE)

N_BACKUPS: Final[int] = 10

SERIES_TABLE: Final[str] = "series"
MOVIES_TABLE: Final[str] = "movies"


class DBRecord(TypedDict):
    id: str
    title: str
    last_season: str
    last_check: str
    last_notified: str
    last_changed: str


def add_id_source_column_if_missing(connection: apsw.Connection) -> None:
    """Add the ``id_source`` column to a series table from before 0.3.0.

    All series that are stored at that point get the ID source 'IMDb'.
    """
    cursor = connection.cursor()
    table_info = cursor.execute(f"""PRAGMA table_info({SERIES_TABLE})""")
    column_names = [row[1] for row in table_info]
    if "id_source" in column_names:
        return
    cursor.execute(
        f"""
        ALTER TABLE {SERIES_TABLE}
        ADD COLUMN id_source TEXT
        DEFAULT 'TMDB';
        """
    )
    cursor.execute(
        f"""
        UPDATE {SERIES_TABLE}
        SET id_source = 'IMDb';
        """
    )
    print(
        "Column 'id_source' was missing from TV Series table. "
        "All existing series have been given the ID source 'IMDb'"
    )


def create_initial_tables(connection: apsw.Connection) -> None:
    """Create the tables that Seasonwatch had before its schema was versioned.

    Tables that already exist are kept, since databases from before the
    versioning have them but still count as version 0.
    """
    cursor = connection.cursor()
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {MOVIES_TABLE} (
            id TEXT NOT NULL PRIMARY KEY UNIQUE,
            title TEXT NOT NULL UNIQUE,
            number_of_checks INGEGER DEFAULT 0,
            last_notified_date TEXT DEFAULT '1970-01-01 00:00:00',
            last_change_date TEXT DEFAULT '1970-01-01 00:00:00'
        );
        """
    )
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {SERIES_TABLE} (
            id TEXT NOT NULL PRIMARY KEY UNIQUE,
            title TEXT NOT NULL UNIQUE,
            last_watched_season INTEGER DEFAULT 0,
            number_of_checks INGEGER DEFAULT 0,
            last_notified_date TEXT DEFAULT '1970-01-01 00:00:00',
            last_change_date TEXT DEFAULT '1970-01-01 00:00:00',
            id_source TEXT DEFAULT 'TMDB'
        );
        """
    )
    add_id_source_column_if_missing(connection)


def remove_id_source_column(connection: apsw.Connection) -> None:
    """Drop the column that says if the ID of a series is from IMDb or TMDB.

    :raises SeasonwatchException: If a series still has an IMDb ID, since
        only Seasonwatch 0.3 can convert those to TMDB IDs.
    """
    cursor = connection.cursor()
    titles_with_imdb_id = []
    for (title,) in cursor.execute(
        f"SELECT title FROM {SERIES_TABLE} WHERE id_source = 'IMDb'"
    ):
        titles_with_imdb_id.append(title)
    if titles_with_imdb_id:
        raise SeasonwatchException(
            "These TV shows still have an IMDb ID, which this version of "
            f"Seasonwatch can't use: {', '.join(titles_with_imdb_id)}. Install "
            "Seasonwatch 0.3.2 and run it once to convert them to TMDB IDs, "
            "then upgrade again. None of your TV shows have been changed."
        )
    cursor.execute(f"ALTER TABLE {SERIES_TABLE} DROP COLUMN id_source")


# The migration at index N takes the database from schema version N to
# N + 1. Released migrations must not be changed, only added to.
SCHEMA_MIGRATIONS: Final[list[Callable[[apsw.Connection], None]]] = [
    create_initial_tables,
    remove_id_source_column,
]


def read_schema_version(connection: apsw.Connection) -> int:
    """Return how many of ``SCHEMA_MIGRATIONS`` the database has been through."""
    for (schema_version,) in connection.cursor().execute("PRAGMA user_version"):
        return int(schema_version)
    raise SeasonwatchException("Couldn't read the schema version of the database.")


def migrate_schema(connection: apsw.Connection) -> None:
    """Bring the database to the schema that this version of Seasonwatch uses.

    Works on a new, empty database as well as on one from any earlier
    version, and does nothing if the database is already up to date.
    Each migration either takes effect completely or not at all.

    :raises SeasonwatchException: If the database was written by a newer
        version of Seasonwatch.
    """
    schema_version = read_schema_version(connection)
    if schema_version > len(SCHEMA_MIGRATIONS):
        raise SeasonwatchException(
            "The database was created by a newer version of Seasonwatch. "
            "Please upgrade Seasonwatch to use it."
        )

    remaining_migrations = SCHEMA_MIGRATIONS[schema_version:]
    for migration in remaining_migrations:
        # Using the connection as a context manager makes a transaction
        # that is rolled back if the migration raises.
        with connection:
            migration(connection)
            schema_version += 1
            connection.cursor().execute(f"PRAGMA user_version = {schema_version}")


class Sql:
    @staticmethod
    def ensure_table() -> None:
        """Create or update the tables in the Seasonwatch database.

        Also creates the directory for the database if it is missing.
        """
        if not DATA_DIRECTORY.exists():
            DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)

        connection = apsw.Connection(DATABASE_PATH)
        migrate_schema(connection)
        connection.close()

    @staticmethod
    def backup_database() -> None:
        """Backup a dated Seasonwatch database.

        Create a backup of the Seasonwatch database and remove the
        oldest backup if there are more than ``N_BACKUPS`` of them.
        """
        if not DATA_DIRECTORY.exists():
            # Nothing to backup if data directory doesn't exist
            return
        if Path(DATABASE_PATH).exists():
            backup_path = Path(
                DATA_DIRECTORY / str(Utils.timestamp() + "_database.sqlite")
            )
            shutil.copyfile(DATABASE_PATH, backup_path)

        dir_content = os.listdir(DATA_DIRECTORY)
        dir_content.remove(DATABASE_FILE)
        dir_content.sort(reverse=True)
        files_to_remove = set(dir_content).difference(set(dir_content[0:N_BACKUPS]))
        for file in files_to_remove:
            if "database" in file:
                os.remove(DATA_DIRECTORY / file)

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
            DELETE FROM {SERIES_TABLE}
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
        """Add or update a record in the series table.

        Adds or updates a series in the series table. Will add if the ID
        doesn't exist. All columns have to be provided.

        :param id: The ID of the series.
        :param title: The user-provided name of the series.
        :param last: The last seen season by the user.
        :param checks: Number of times this TV show has been checked for
            new seasons. 1 will be added when calling this function, so
            please simply send back whatever value was there before for
            this record.
        :param last_change: Last time this series was updated in the
            database.
        :param last_notify: Last time the user was notified about the
            status of new seasons for this series.
        """
        connection = apsw.Connection(DATABASE_PATH)
        cursor = connection.cursor()

        checks = checks + 1

        cursor.execute("BEGIN TRANSACTION")
        cursor.execute(
            f"""
            INSERT OR REPLACE INTO {SERIES_TABLE} (
                id,
                title,
                last_watched_season,
                number_of_checks,
                last_notified_date,
                last_change_date
            )
            VALUES(
                {id},
                '{title}',
                {last},
                {checks},
                '{last_notify}',
                '{last_change}'
            );
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
            UPDATE {SERIES_TABLE}
            SET last_watched_season = last_watched_season + 1,
                last_change_date = '{Utils.sql_today()}'
            WHERE id = {id};
            """
        cursor.execute(transaction)
        cursor.execute("COMMIT TRANSACTION")
        connection.close()

    @staticmethod
    def read_series(id: str) -> dict[str, str]:
        """Return data from the database for the season with id `id`"""
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
                {SERIES_TABLE}
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
        connection.close()
        return values

    @staticmethod
    def read_all_series() -> list[DBRecord]:
        """Return data from the database for every TV show registered.

        Read all data about TV shows in the database, including data
        about id, last watched season, number of checks, etc.
        """
        connection = apsw.Connection(DATABASE_PATH)
        cursor = connection.cursor()
        values: list[DBRecord] = []
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
                {SERIES_TABLE}
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
                'https://www.themoviedb.org/tv/' || id
            FROM
                {SERIES_TABLE};
            """
        )
        table = from_db_cursor(cursor)
        if table is None:
            raise SeasonwatchException("Couldn't create table from database cursor")

        table.field_names = [
            "Title",
            "Last watched season",
            "Hyperlink",
        ]
        connection.close()
        return table
