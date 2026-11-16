import sys
from datetime import datetime, time, timedelta

from requests import HTTPError, RequestException, Session

from seasonwatch.constants import Constants, Source
from seasonwatch.exceptions import SeasonwatchException
from seasonwatch.sql import Sql
from seasonwatch.tmdb import fetch_season
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
        except RequestException as e:
            print(f"There was an error fetching {url}: {e}")
            sys.exit(1)
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

    def convert_imdb_series(self, session: Session) -> None:
        """Interactively replace the IMDb IDs of stored series with TMDB IDs.

        Asks the user to confirm or enter the TMDB ID of every series
        that still has an IMDb ID. Series that the user skips keep their
        IMDb ID.
        """
        last_change = Utils.sql_today()
        last_notify = Utils.sql_today()
        for series in Sql.read_all_series():
            if series["id_source"] != Source.IMDB:
                continue
            name = series["title"]
            checks = int(series.get("last_check", 0)) + 1
            tmdb_id, tmdb_name = self.translate_imdb_id(session, series["id"])
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
            Sql.update_series(
                id=tmdb_id,
                title=name,
                last=int(series["last_season"]),
                checks=checks,
                last_change=last_change,
                last_notify=last_notify,
                id_source=Source.TMDB,
                full_replace=True,
            )
            print(f"Successfully migrated series '{name}' from IMDb to TMDB")

    def check_for_new_seasons(
        self,
        session: Session,
    ) -> None:
        """
        Look through the seasons in the database, and check on TMDB
        whether there is a new season coming up, or one that has already
        come out. Series that still have an IMDb ID are converted first,
        and left out if the user skips converting them.
        """
        self.convert_imdb_series(session)
        for series in Sql.read_all_series():
            if series["id_source"] == Source.IMDB:
                # Only IDs from TMDB can be looked up there.
                continue
            last_watched_season = int(series["last_season"])
            next_season_no = last_watched_season + 1
            name = series["title"]
            id = series["id"]

            next_season = fetch_season(session, id, next_season_no)

            if next_season is None:
                message = f"No season {next_season_no} found for {name}"
                self.series["nothing"][name] = message
                continue

            if next_season.air_date is None:
                message = (
                    f"Season {next_season_no} of {name} coming up, the release "
                    "date is unknown"
                )
                self.series["nothing"][name] = message
                continue

            next_air_date = datetime.combine(next_season.air_date, time.min)

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
