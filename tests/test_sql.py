import apsw
import pytest

from seasonwatch.exceptions import SeasonwatchException
from seasonwatch.sql import SCHEMA_MIGRATIONS, migrate_schema, read_schema_version


def create_empty_database() -> apsw.Connection:
    return apsw.Connection(":memory:")


def read_column_names(connection: apsw.Connection, table: str) -> list[str]:
    column_names = []
    for row in connection.cursor().execute(f"PRAGMA table_info({table})"):
        column_names.append(row[1])
    return column_names


def test_migrating_new_database_reaches_latest_schema_version() -> None:
    connection = create_empty_database()

    migrate_schema(connection)

    assert read_schema_version(connection) == len(SCHEMA_MIGRATIONS)
    assert "title" in read_column_names(connection, "series")


def test_migrating_twice_changes_nothing() -> None:
    connection = create_empty_database()
    migrate_schema(connection)
    connection.cursor().execute(
        "INSERT INTO series (id, title) VALUES ('63639', 'The Expanse')"
    )

    migrate_schema(connection)

    all_titles = list(connection.cursor().execute("SELECT title FROM series"))
    assert all_titles == [("The Expanse",)]


def test_migrating_database_from_newer_version_is_refused() -> None:
    connection = create_empty_database()
    newer_schema_version = len(SCHEMA_MIGRATIONS) + 1
    connection.cursor().execute(f"PRAGMA user_version = {newer_schema_version}")

    with pytest.raises(SeasonwatchException):
        migrate_schema(connection)


def create_database_at_schema_version_1() -> apsw.Connection:
    connection = create_empty_database()
    first_migration = SCHEMA_MIGRATIONS[0]
    first_migration(connection)
    connection.cursor().execute("PRAGMA user_version = 1")
    return connection


def test_migrating_drops_id_source_when_all_ids_are_from_tmdb() -> None:
    connection = create_database_at_schema_version_1()
    connection.cursor().execute(
        "INSERT INTO series (id, title, id_source) "
        "VALUES ('63639', 'The Expanse', 'TMDB')"
    )

    migrate_schema(connection)

    assert "id_source" not in read_column_names(connection, "series")
    all_titles = list(connection.cursor().execute("SELECT title FROM series"))
    assert all_titles == [("The Expanse",)]


def test_migrating_is_refused_while_a_series_has_an_imdb_id() -> None:
    connection = create_database_at_schema_version_1()
    connection.cursor().execute(
        "INSERT INTO series (id, title, id_source) "
        "VALUES ('3230854', 'The Expanse', 'IMDb')"
    )

    with pytest.raises(SeasonwatchException, match="The Expanse"):
        migrate_schema(connection)

    assert read_schema_version(connection) == 1
    assert "id_source" in read_column_names(connection, "series")
