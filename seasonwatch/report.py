"""Telling the user what checking for new seasons resulted in."""

import gi

gi.require_version("Notify", "0.7")

from gi.repository import Notify

from seasonwatch.presentation import PRESENTATION_BY_STATUS, describe_season_check
from seasonwatch.season_status import SeasonCheck


def report_season_checks(season_checks: list[SeasonCheck]) -> None:
    """Print all season checks and show notifications for the urgent ones.

    The checks are grouped by status, in the order that the statuses
    have in ``PRESENTATION_BY_STATUS``, which also says which of them
    get a desktop notification.
    """
    Notify.init("Seasonwatch")

    for status_type, presentation in PRESENTATION_BY_STATUS.items():
        for season_check in season_checks:
            if type(season_check.status) is not status_type:
                continue

            message = describe_season_check(season_check)
            print(presentation.terminal_color + message)

            if not presentation.shows_notification:
                continue
            notification = Notify.Notification.new(season_check.series_title, message)
            timeout = presentation.notification_timeout_in_milliseconds
            if timeout is not None:
                notification.set_timeout(timeout)
            notification.show()
