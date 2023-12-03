from datetime import datetime, timedelta

from dateutil.parser import parse
from requests import HTTPError, Session

from seasonwatch.constants import Constants, Source
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

    def translate_imdb_id(
        self,
        session: Session,
        imdb_id: str,
    ) -> tuple[str | None, str | None]:
        """Suggest TMDB ID with corresponding name for given IMDb ID."""
        imdb_id = f"tt{imdb_id:0>7}"
        url = f"{Constants.API_BASE_URL}/find/{imdb_id}?external_source=imdb_id"
        try:
            response = session.get(url)
            response.raise_for_status()
        except HTTPError as e:
            raise SeasonwatchException(
                f"Failure connecting to TMDB for converting IMDb ID: {e}"
            )
        response = response.json()
        if not isinstance(response, dict):
            raise SeasonwatchException(
                "Malformed data returned from TMDB when attemping to find TMDB ID."
            )
        tv_results_list = response.get("tv_results")
        if not tv_results_list or not len(tv_results_list) > 0:
            return None, None
        tv_result = tv_results_list[0]

        title = tv_result.get("original_name")
        id = tv_result.get("id")
        return id, title

    def check_for_new_seasons(
        self,
        session: Session,
    ) -> None:
        """
        Look through the seasons in the database, and check on IMDb
        whether there is a new season coming up, or one that has already
        come out. This is notified as desktop notification for the more
        important ones, and information about all series is also
        returned for further use.
        """
        series_data = Sql.read_all_series()
        last_change = Utils.sql_today()
        last_notify = Utils.sql_today()
        for series in series_data:
            last_watched_season = int(series["last_season"])
            checks = int(series.get("last_check", 0)) + 1
            next_season_no = last_watched_season + 1
            name = series["title"]
            id = series["id"]
            source = series["id_source"]
            if source == Source.IMDB:
                tmdb_id, tmdb_name = self.translate_imdb_id(session, id)
                print(f"Attempting to convert ID from IMDb to TMDB for series: {name}")
                looks_ok = False
                if tmdb_id:
                    print(f"Found TMDB ID {tmdb_id} with associated name '{tmdb_name}'")
                    looks_ok = input("Does it look okay? [Y/n]: ") not in ["n", "N"]
                if not looks_ok or not tmdb_id:
                    print("Couldn't automatically find the ID for above series.")
                    print("Please enter it manually (after tv/ in TMDB URL): ")
                    tmdb_id = input("TMDB ID (empty skips for now): ")
                    if tmdb_id == "":
                        print(f"Skipping '{name}'...")
                        continue
                id = tmdb_id
                source = Source.TMDB
                Sql.update_series(
                    id=id,
                    title=name,
                    last=last_watched_season,
                    checks=checks,
                    last_change=last_change,
                    last_notify=last_notify,
                    id_source=source,
                    full_replace=True,
                )
                print(f"Successfully migrated series '{name}' from IMDb to TMDB")

            next_season = Utils.get_next_season(id, last_watched_season, session)

            if not next_season:
                message = f"No season {next_season_no} found for {name}"
                self.series["nothing"][name] = message
                continue

            next_air_date_raw = next_season.get("air_date")
            if not next_air_date_raw:
                message = (
                    f"Season {next_season_no} of {name} coming up, the release "
                    "date is unknown"
                )
                self.series["nothing"][name] = message
            if not isinstance(next_air_date_raw, str):
                raise SeasonwatchException(
                    f"Malformed air date returned from TMDB: {next_air_date_raw}"
                )
            next_air_date = parse(next_air_date_raw)

            # The new season is out
            if next_air_date < datetime.now():
                message = f"Season {next_season_no} of {name} is out already!"
                self.series["new"][name] = message
            # The new season is not yet out
            elif next_air_date < datetime.now() + timedelta(days=90):
                message = (
                    f"Season {next_season_no} of {name} is not yet out but "
                    f"will be released on {next_air_date.strftime('%B %-d, %Y')}."
                )
                self.series["soon"][name] = message
            else:
                message = (
                    f"Season {next_season_no} of {name} coming up, in more "
                    "than three months"
                )
                self.series["later"][name] = message

            Sql.update_series(
                id,
                name,
                last_watched_season,
                checks,
                last_change,
                last_notify,
                source,
            )
