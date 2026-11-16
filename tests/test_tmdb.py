from datetime import date

import pytest

from seasonwatch.exceptions import SeasonwatchException
from seasonwatch.tmdb import Season, find_season, parse_season


def test_parse_season_with_air_date() -> None:
    season = parse_season({"season_number": 4, "air_date": "2019-12-13"})

    assert season == Season(number=4, air_date=date(2019, 12, 13))


@pytest.mark.parametrize("air_date_from_tmdb", [None, ""])
def test_parse_season_without_air_date(air_date_from_tmdb: str | None) -> None:
    season = parse_season({"season_number": 4, "air_date": air_date_from_tmdb})

    assert season == Season(number=4, air_date=None)


def test_parse_season_where_air_date_is_left_out() -> None:
    season = parse_season({"season_number": 4})

    assert season == Season(number=4, air_date=None)


@pytest.mark.parametrize(
    "malformed_season_data",
    [
        "not a season",
        {"air_date": "2019-12-13"},
        {"season_number": "4", "air_date": "2019-12-13"},
        {"season_number": 4, "air_date": "December 13, 2019"},
        {"season_number": 4, "air_date": 20191213},
    ],
)
def test_parse_season_rejects_malformed_data(malformed_season_data: object) -> None:
    with pytest.raises(SeasonwatchException):
        parse_season(malformed_season_data)


def test_find_season_returns_the_requested_season() -> None:
    series_data = {
        "seasons": [
            {"season_number": 0, "air_date": "2015-11-23"},
            {"season_number": 1, "air_date": "2015-12-14"},
            {"season_number": 2, "air_date": "2017-02-01"},
        ]
    }

    season = find_season(series_data, season_number=2)

    assert season == Season(number=2, air_date=date(2017, 2, 1))


def test_find_season_returns_none_for_unlisted_season() -> None:
    series_data = {"seasons": [{"season_number": 1, "air_date": "2015-12-14"}]}

    assert find_season(series_data, season_number=2) is None


def test_find_season_ignores_malformed_data_for_other_seasons() -> None:
    series_data = {
        "seasons": [
            {"season_number": 1, "air_date": "not a date"},
            {"season_number": 2, "air_date": "2017-02-01"},
        ]
    }

    season = find_season(series_data, season_number=2)

    assert season == Season(number=2, air_date=date(2017, 2, 1))


@pytest.mark.parametrize("malformed_series_data", [[], {}, {"seasons": None}])
def test_find_season_rejects_malformed_series(malformed_series_data: object) -> None:
    with pytest.raises(SeasonwatchException):
        find_season(malformed_series_data, season_number=1)
