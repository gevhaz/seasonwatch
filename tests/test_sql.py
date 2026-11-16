import apsw
import pytest

from seasonwatch.exceptions import SeasonwatchException
from seasonwatch.series import Series
from seasonwatch.sql import (
    SCHEMA_MIGRATIONS,
    add_series,
    migrate_schema,
    read_all_series,
    read_schema_version,
    remove_series,
    step_up_series,
)

THE_EXPANSE = Series(tmdb_id=63639, title="The Expanse", last_watched_season=3)
GAME_OF_THRONES = Series(tmdb_id=1399, title="Game of Thrones", last_watched_season=8)


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
        "INSERT INTO series (tmdb_id, title, last_watched_season) "
        "VALUES (63639, 'The Expanse', 3)"
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


def create_database_at_schema_version(schema_version: int) -> apsw.Connection:
    connection = create_empty_database()
    for migration in SCHEMA_MIGRATIONS[:schema_version]:
        migration(connection)
    connection.cursor().execute(f"PRAGMA user_version = {schema_version}")
    return connection


def test_migrating_drops_id_source_when_all_ids_are_from_tmdb() -> None:
    connection = create_database_at_schema_version(1)
    connection.cursor().execute(
        "INSERT INTO series (id, title, id_source) "
        "VALUES ('63639', 'The Expanse', 'TMDB')"
    )

    remove_id_source_column = SCHEMA_MIGRATIONS[1]
    remove_id_source_column(connection)

    assert "id_source" not in read_column_names(connection, "series")
    all_titles = list(connection.cursor().execute("SELECT title FROM series"))
    assert all_titles == [("The Expanse",)]


def test_migrating_is_refused_while_a_series_has_an_imdb_id() -> None:
    connection = create_database_at_schema_version(1)
    connection.cursor().execute(
        "INSERT INTO series (id, title, id_source) "
        "VALUES ('3230854', 'The Expanse', 'IMDb')"
    )

    with pytest.raises(SeasonwatchException, match="The Expanse"):
        migrate_schema(connection)

    assert read_schema_version(connection) == 1
    assert "id_source" in read_column_names(connection, "series")


def test_migrating_keeps_series_in_order_with_numeric_ids() -> None:
    connection = create_database_at_schema_version(2)
    connection.cursor().execute(
        "INSERT INTO series (id, title, last_watched_season, number_of_checks) "
        "VALUES ('63639', 'The Expanse', 3, 7), ('1399', 'Game of Thrones', 8, 2)"
    )

    migrate_schema(connection)

    all_rows = list(connection.cursor().execute("SELECT * FROM series ORDER BY rowid"))
    assert all_rows == [(63639, "The Expanse", 3), (1399, "Game of Thrones", 8)]


def test_migrating_is_refused_while_a_series_has_a_malformed_id() -> None:
    connection = create_database_at_schema_version(2)
    connection.cursor().execute(
        "INSERT INTO series (id, title) VALUES ('1399-game-of-thrones', 'GoT')"
    )

    with pytest.raises(SeasonwatchException, match="GoT"):
        migrate_schema(connection)

    assert read_schema_version(connection) == 2
    assert "id" in read_column_names(connection, "series")


def test_migrating_database_from_before_versioning_keeps_its_series() -> None:
    connection = create_database_at_schema_version(1)
    connection.cursor().execute("PRAGMA user_version = 0")
    connection.cursor().execute(
        "INSERT INTO series (id, title, last_watched_season, id_source) "
        "VALUES ('63639', 'The Expanse', 3, 'TMDB')"
    )

    migrate_schema(connection)

    all_rows = list(connection.cursor().execute("SELECT * FROM series"))
    assert all_rows == [(63639, "The Expanse", 3)]
    assert read_schema_version(connection) == len(SCHEMA_MIGRATIONS)


def create_up_to_date_database() -> apsw.Connection:
    connection = create_empty_database()
    migrate_schema(connection)
    return connection


def test_added_series_are_read_in_the_order_they_were_added() -> None:
    connection = create_up_to_date_database()

    add_series(connection, THE_EXPANSE)
    add_series(connection, GAME_OF_THRONES)

    assert read_all_series(connection) == [THE_EXPANSE, GAME_OF_THRONES]


def test_title_with_apostrophe_is_stored_unchanged() -> None:
    connection = create_up_to_date_database()
    greys_anatomy = Series(tmdb_id=1416, title="Grey's Anatomy", last_watched_season=1)

    add_series(connection, greys_anatomy)

    assert read_all_series(connection) == [greys_anatomy]


def test_step_up_series_increases_only_that_series() -> None:
    connection = create_up_to_date_database()
    add_series(connection, THE_EXPANSE)
    add_series(connection, GAME_OF_THRONES)

    step_up_series(connection, THE_EXPANSE.tmdb_id)

    stepped_up_expanse = Series(
        tmdb_id=63639,
        title="The Expanse",
        last_watched_season=4,
    )
    assert read_all_series(connection) == [stepped_up_expanse, GAME_OF_THRONES]


def test_remove_series_removes_only_that_series() -> None:
    connection = create_up_to_date_database()
    add_series(connection, THE_EXPANSE)
    add_series(connection, GAME_OF_THRONES)

    remove_series(connection, THE_EXPANSE.tmdb_id)

    assert read_all_series(connection) == [GAME_OF_THRONES]
