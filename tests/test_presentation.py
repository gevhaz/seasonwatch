from datetime import date
from typing import get_args

import pytest

from seasonwatch.presentation import PRESENTATION_BY_STATUS, describe_season_check
from seasonwatch.season_status import (
    ComingLater,
    ComingSoon,
    NotAnnounced,
    Released,
    SeasonCheck,
    SeasonStatus,
    Unscheduled,
)


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
