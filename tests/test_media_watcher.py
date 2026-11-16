from datetime import date

import apsw
import pytest
from requests import Session

from seasonwatch import media_watcher
from seasonwatch.exceptions import SeasonwatchException
from seasonwatch.season_status import CheckFailed, Released, SeasonCheck
from seasonwatch.series import Series
from seasonwatch.sql import add_series, migrate_schema
from seasonwatch.tmdb import Season

TODAY = date(2024, 1, 31)
ID_THAT_TMDB_DOES_NOT_HAVE = 999


def fetch_season_without_network(
    session: Session,
    series_id: int,
    season_number: int,
) -> Season | None:
    if series_id == ID_THAT_TMDB_DOES_NOT_HAVE:
        raise SeasonwatchException("404 Client Error")
    return Season(number=season_number, air_date=date(2023, 6, 1))


def test_failed_check_does_not_stop_the_other_series_from_being_checked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(media_watcher, "fetch_season", fetch_season_without_network)
    connection = apsw.Connection(":memory:")
    migrate_schema(connection)
    add_series(
        connection,
        Series(
            tmdb_id=ID_THAT_TMDB_DOES_NOT_HAVE,
            title="Mistyped",
            last_watched_season=1,
        ),
    )
    add_series(
        connection,
        Series(tmdb_id=63639, title="The Expanse", last_watched_season=3),
    )

    season_checks = media_watcher.check_for_new_seasons(
        connection,
        Session(),
        today=TODAY,
    )

    assert season_checks == [
        SeasonCheck(
            series_title="Mistyped",
            season_number=2,
            status=CheckFailed(reason="404 Client Error"),
        ),
        SeasonCheck(
            series_title="The Expanse",
            season_number=4,
            status=Released(air_date=date(2023, 6, 1)),
        ),
    ]
