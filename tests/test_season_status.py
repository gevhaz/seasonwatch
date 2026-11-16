from datetime import date

from seasonwatch.season_status import (
    ComingLater,
    ComingSoon,
    NotAnnounced,
    Released,
    Unscheduled,
    classify_season,
)
from seasonwatch.tmdb import Season

TODAY = date(2024, 1, 31)


def classify_season_airing_on(air_date: date) -> object:
    return classify_season(Season(number=2, air_date=air_date), today=TODAY)


def test_season_that_tmdb_does_not_list_is_not_announced() -> None:
    assert classify_season(None, today=TODAY) == NotAnnounced()


def test_season_without_air_date_is_unscheduled() -> None:
    season = Season(number=2, air_date=None)

    assert classify_season(season, today=TODAY) == Unscheduled()


def test_season_that_aired_earlier_is_released() -> None:
    air_date = date(2023, 6, 1)

    assert classify_season_airing_on(air_date) == Released(air_date)


def test_season_that_airs_today_is_released() -> None:
    assert classify_season_airing_on(TODAY) == Released(TODAY)


def test_season_that_airs_tomorrow_is_coming_soon() -> None:
    air_date = date(2024, 2, 1)

    assert classify_season_airing_on(air_date) == ComingSoon(air_date)


def test_season_that_airs_in_90_days_is_coming_soon() -> None:
    air_date = date(2024, 4, 30)

    assert classify_season_airing_on(air_date) == ComingSoon(air_date)


def test_season_that_airs_in_91_days_is_coming_later() -> None:
    air_date = date(2024, 5, 1)

    assert classify_season_airing_on(air_date) == ComingLater(air_date)
