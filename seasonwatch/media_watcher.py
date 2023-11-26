from datetime import datetime, timedelta

from imdb.parser.http import IMDbHTTPAccessSystem

from seasonwatch.constants import Source
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
        ia: IMDbHTTPAccessSystem,
    ) -> None:
        """
        Look through the seasons in the database, and check on IMDb
        whether there is a new season coming up, or one that has already
        come out. This is notified as desktop notification for the more
        important ones, and information about all series is also
        returned for further use.
        """
        series_data = Sql.read_all_series()
        for series in series_data:
            last_watched_season = int(series["last_season"])
            next_season = last_watched_season + 1
            name = series["title"]
            id = series["id"]
            source = series["id_source"]
            if source == Source.TMDB:
                print(f"TMDB not yet supported. Skipping '{name}'")
                continue

            old_data = Sql.read_series(id)

            last_change = Utils.sql_today()
            last_notify = Utils.sql_today()
            Sql.update_series(
                id,
                name,
                last_watched_season,
                int(old_data.get("last_season", 0)),
                last_change,
                last_notify,
                source,
            )

            try:
                next_episode_id = Utils.get_next_episode_id(id, last_watched_season, ia)
            except SeasonwatchException as e:
                self.series["nothing"][name] = f"{name}: {str(e)}"
                continue

            if next_episode_id is None:
                self.series["nothing"][
                    name
                ] = f"No season {next_season} found for {name}"
                continue

            try:
                next_season_earliest_release = Utils.get_next_release_date(
                    name,
                    next_season,
                    next_episode_id,
                    ia,
                )
            except SeasonwatchException:
                self.series["nothing"][name] = (
                    f"Season {next_season} of {name} is announced but there is no "
                    "release date yet"
                )
                continue

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
