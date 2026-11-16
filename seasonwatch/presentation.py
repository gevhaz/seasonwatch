"""How the result of checking for new seasons is worded and displayed.

Nothing here prints or notifies, so it can be used without the desktop
notification library.
"""

from dataclasses import dataclass
from typing import Final

from colorama import Fore

from seasonwatch.season_status import (
    CheckFailed,
    ComingLater,
    ComingSoon,
    NotAnnounced,
    Released,
    SeasonCheck,
    Unscheduled,
    assert_never,
)


@dataclass(frozen=True)
class Presentation:
    """How season checks with a certain status are shown to the user."""

    # Colorama code that the line in the terminal is prefixed with.
    terminal_color: str
    shows_notification: bool
    # None leaves the timeout up to the notification server.
    notification_timeout_in_milliseconds: int | None = None
    # Errors are printed to standard error instead of standard output.
    is_error: bool = False


# The statuses are listed in the terminal in the order they have here.
PRESENTATION_BY_STATUS: Final[dict[type, Presentation]] = {
    Released: Presentation(
        terminal_color=Fore.BLUE,
        shows_notification=True,
        notification_timeout_in_milliseconds=10000,
    ),
    ComingSoon: Presentation(terminal_color=Fore.GREEN, shows_notification=True),
    ComingLater: Presentation(terminal_color="", shows_notification=False),
    Unscheduled: Presentation(terminal_color="", shows_notification=False),
    NotAnnounced: Presentation(terminal_color="", shows_notification=False),
    CheckFailed: Presentation(
        terminal_color=Fore.RED,
        shows_notification=False,
        is_error=True,
    ),
}


def describe_season_check(season_check: SeasonCheck) -> str:
    """Return the sentence that tells the user about a checked season.

    For example "Season 4 of The Expanse is out already!".
    """
    season_number = season_check.season_number
    series_title = season_check.series_title
    status = season_check.status

    if isinstance(status, Released):
        return f"Season {season_number} of {series_title} is out already!"
    if isinstance(status, ComingSoon):
        air_date_text = status.air_date.strftime("%B %-d, %Y")
        return (
            f"Season {season_number} of {series_title} is not yet out but "
            f"will be released on {air_date_text}."
        )
    if isinstance(status, ComingLater):
        return (
            f"Season {season_number} of {series_title} coming up, in more "
            "than three months"
        )
    if isinstance(status, Unscheduled):
        return (
            f"Season {season_number} of {series_title} coming up, the release "
            "date is unknown"
        )
    if isinstance(status, NotAnnounced):
        return f"No season {season_number} found for {series_title}"
    if isinstance(status, CheckFailed):
        return (
            f"Couldn't check for season {season_number} of {series_title}: "
            f"{status.reason}"
        )
    assert_never(status)
