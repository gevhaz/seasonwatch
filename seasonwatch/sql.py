import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable, Final

import apsw

from seasonwatch.exceptions import SeasonwatchException
from seasonwatch.series import Series

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


def rebuild_series_table(connection: apsw.Connection) -> None:
    """Keep only the used columns of the series table, with numeric IDs.

    The ID, the title and the last watched season of every series are
    kept, as is the order of the series. The columns that recorded
    checks and notifications are dropped, and so is the movies table
    if it is empty. Neither was ever read.

    :raises SeasonwatchException: If the ID of a series isn't a number.
    """
    cursor = connection.cursor()

    titles_with_malformed_id = []
    for (title,) in cursor.execute(
        f"SELECT title FROM {SERIES_TABLE} WHERE id = '' OR id GLOB '*[^0-9]*'"
    ):
        titles_with_malformed_id.append(title)
    if titles_with_malformed_id:
        raise SeasonwatchException(
            "These TV shows have an ID that isn't a number: "
            f"{', '.join(titles_with_malformed_id)}. Remove them with the "
            "version of Seasonwatch that you had before and add them again. "
            "None of your TV shows have been changed."
        )

    # SQLite can't change the type of a column, so the table is replaced.
    # The ID isn't the primary key, because that would make it the rowid
    # that keeps track of the order in which the series were added.
    cursor.execute(
        """
        CREATE TABLE rebuilt_series (
            tmdb_id INTEGER NOT NULL UNIQUE,
            title TEXT NOT NULL UNIQUE,
            last_watched_season INTEGER NOT NULL
        );
        """
    )
    cursor.execute(
        f"""
        INSERT INTO rebuilt_series (tmdb_id, title, last_watched_season)
        SELECT CAST(id AS INTEGER), title, COALESCE(last_watched_season, 0)
        FROM {SERIES_TABLE}
        ORDER BY rowid;
        """
    )
    cursor.execute(f"DROP TABLE {SERIES_TABLE}")
    cursor.execute(f"ALTER TABLE rebuilt_series RENAME TO {SERIES_TABLE}")

    for (number_of_movies,) in cursor.execute(f"SELECT COUNT(*) FROM {MOVIES_TABLE}"):
        if number_of_movies == 0:
            cursor.execute(f"DROP TABLE {MOVIES_TABLE}")


# The migration at index N takes the database from schema version N to
# N + 1. Released migrations must not be changed, only added to.
SCHEMA_MIGRATIONS: Final[list[Callable[[apsw.Connection], None]]] = [
    create_initial_tables,
    remove_id_source_column,
    rebuild_series_table,
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


def ensure_table() -> None:
    """Create or update the tables in the Seasonwatch database.

    Also creates the directory for the database if it is missing.
    """
    if not DATA_DIRECTORY.exists():
        DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)

    connection = apsw.Connection(DATABASE_PATH)
    migrate_schema(connection)
    connection.close()


def backup_database() -> None:
    """Backup a dated Seasonwatch database.

    Create a backup of the Seasonwatch database and remove the
    oldest backup if there are more than ``N_BACKUPS`` of them.
    """
    if not DATA_DIRECTORY.exists():
        # Nothing to backup if data directory doesn't exist
        return
    if Path(DATABASE_PATH).exists():
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_path = DATA_DIRECTORY / f"{timestamp}_database.sqlite"
        shutil.copyfile(DATABASE_PATH, backup_path)

    dir_content = os.listdir(DATA_DIRECTORY)
    dir_content.remove(DATABASE_FILE)
    dir_content.sort(reverse=True)
    files_to_remove = set(dir_content).difference(set(dir_content[0:N_BACKUPS]))
    for file in files_to_remove:
        if "database" in file:
            os.remove(DATA_DIRECTORY / file)


def add_series(series: Series) -> None:
    """Store a series, replacing any stored series with its ID or title."""
    connection = apsw.Connection(DATABASE_PATH)
    with connection:
        connection.cursor().execute(
            f"""
            INSERT OR REPLACE INTO {SERIES_TABLE} (
                tmdb_id,
                title,
                last_watched_season
            )
            VALUES(?, ?, ?);
            """,
            (series.tmdb_id, series.title, series.last_watched_season),
        )
    connection.close()


def remove_series(tmdb_id: int) -> None:
    """Remove the series with the given ID, if there is one."""
    connection = apsw.Connection(DATABASE_PATH)
    with connection:
        connection.cursor().execute(
            f"DELETE FROM {SERIES_TABLE} WHERE tmdb_id = ?;",
            (tmdb_id,),
        )
    connection.close()


def step_up_series(tmdb_id: int) -> None:
    """Increase the last watched season of the series with the ID by one."""
    connection = apsw.Connection(DATABASE_PATH)
    with connection:
        connection.cursor().execute(
            f"""
            UPDATE {SERIES_TABLE}
            SET last_watched_season = last_watched_season + 1
            WHERE tmdb_id = ?;
            """,
            (tmdb_id,),
        )
    connection.close()


def read_all_series() -> list[Series]:
    """Return all stored series, in the order that they were added."""
    connection = apsw.Connection(DATABASE_PATH)
    all_series = []
    for tmdb_id, title, last_watched_season in connection.cursor().execute(
        f"""
        SELECT tmdb_id, title, last_watched_season
        FROM {SERIES_TABLE}
        ORDER BY rowid;
        """
    ):
        all_series.append(
            Series(
                tmdb_id=tmdb_id,
                title=title,
                last_watched_season=last_watched_season,
            )
        )
    connection.close()
    return all_series
