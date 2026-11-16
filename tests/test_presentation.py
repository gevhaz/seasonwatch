from datetime import date
from typing import get_args

import pytest

from seasonwatch.presentation import (
    PRESENTATION_BY_STATUS,
    describe_season_check,
    format_series_table,
)
from seasonwatch.season_status import (
    CheckFailed,
    ComingLater,
    ComingSoon,
    NotAnnounced,
    Released,
    SeasonCheck,
    SeasonStatus,
    Unscheduled,
)
from seasonwatch.series import Series


def test_every_status_has_a_presentation() -> None:
    all_status_types = set(get_args(SeasonStatus))

    assert set(PRESENTATION_BY_STATUS) == all_status_types


@pytest.mark.parametrize(
    ["status", "expected_description"],
    [
        (
            Released(air_date=date(2019, 12, 13)),
            "Season 4 of The Expanse is out already!",
        ),
        (
            ComingSoon(air_date=date(2019, 12, 3)),
            "Season 4 of The Expanse is not yet out but will be released on "
            "December 3, 2019.",
        ),
        (
            ComingLater(air_date=date(2019, 12, 13)),
            "Season 4 of The Expanse coming up, in more than three months",
        ),
        (
            Unscheduled(),
            "Season 4 of The Expanse coming up, the release date is unknown",
        ),
        (
            NotAnnounced(),
            "No season 4 found for The Expanse",
        ),
        (
            CheckFailed(reason="404 Client Error"),
            "Couldn't check for season 4 of The Expanse: 404 Client Error",
        ),
    ],
)
def test_describe_season_check(
    status: SeasonStatus,
    expected_description: str,
) -> None:
    season_check = SeasonCheck(
        series_title="The Expanse",
        season_number=4,
        status=status,
    )

    assert describe_season_check(season_check) == expected_description


def test_format_series_table_links_to_tmdb() -> None:
    series = Series(tmdb_id=63639, title="The Expanse", last_watched_season=3)

    table = format_series_table([series])

    row_of_the_series = table.splitlines()[3]
    cells = [cell.strip() for cell in row_of_the_series.strip("│").split("│")]
    assert cells == ["The Expanse", "3", "https://www.themoviedb.org/tv/63639"]
