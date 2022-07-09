from datetime import date, datetime, timedelta

from imdb.parser.http import IMDbHTTPAccessSystem

from seasonwatch.exceptions import SeasonwatchException
from seasonwatch.sql import Sql
from seasonwatch.utils import Utils


class MediaWatcher:
    """
    Class for checking for new media given a config
    """

    def __init__(self) -> None:
        self.series: dict[str, dict[str, str]] = {
            "new": {},
            "soon": {},
            "later": {},
            "nothing": {},
        }

    def check_for_new_seasons(
        self,
        series_config: dict[str, str],
        ia: IMDbHTTPAccessSystem,
    ) -> None:
        last_watched_season = int(series_config["current_season"])
        next_season = last_watched_season + 1
        name = series_config["title"]
        id = series_config["id"]

        old_data = Sql.read_series(id)

        last_change = date.strftime(date.today(), "%Y-%m-%d 00:00:00")
        Sql.update_series(
            id,
            name,
            last_watched_season,
            int(old_data.get("last_season", 0)),
            last_change,
        )

        try:
            next_episode_id = Utils.get_next_episode_id(id, last_watched_season, ia)
        except SeasonwatchException as e:
            self.series["nothing"][name] = f"{name}: {str(e)}"
            return None

        if next_episode_id is None:
            self.series["nothing"][name] = f"No season {next_season} found for {name}"
            return None

        try:
            next_season_earliest_release = Utils.get_next_release_date(
                name,
                next_season,
                next_episode_id,
                ia,
            )
        except SeasonwatchException:
            self.series["nothing"][name] = (
                f"Season {next_season} of {name} is announced but there is no release "
                "date yet"
            )
            return None

        # The new season is out
        if next_season_earliest_release < datetime.now():
            message = f"Season {next_season} of {name} is out already!"
            self.series["new"][name] = message
        # The new season is not yet out
        elif next_season_earliest_release < datetime.now() + timedelta(days=90):
            message = (
                f"Season {next_season} of {name} is not yet out but "
                "will be released on "
                f"{next_season_earliest_release.strftime('%B %-d, %Y')}."
            )
            self.series["soon"][name] = message
        else:
            message = (
                f"Season {next_season} of {name} coming up, in more "
                "than three months"
            )
            self.series["later"][name] = message

        return None
