from datetime import datetime, timedelta
from typing import Any

import discogs_client
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

        self.music: dict[str, dict[str, str]] = {
            "new": {},
            "recent": {},
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

    def check_for_new_music(self, discogs_token: str | None) -> None:
        artists = Sql.read_all_artists()
        music_data = Sql.read_all_music()

        if len(artists) > 0 and discogs_token is None:
            raise SeasonwatchException(
                "Cannot check for new music since no discogs API token was found."
            )

        d = discogs_client.Client(
            "Seasonwatch",
            user_token=discogs_token,
        )

        for artist in artists:
            artist_id = artist["id"]
            old_albums = [a for a in music_data if a["artist_id"] == artist_id]
            fetched_albums: list[Any] = []

            # Create discogs searches
            artist_search = d.artist(artist["id"])
            release_search = artist_search.releases

            # Determine number of pages in search results
            n_discogs_pages = release_search.pages
            if not isinstance(n_discogs_pages, int):
                raise SeasonwatchException(
                    "Couldn't get number of pages of albums from discogs."
                )

            # Load search result into fetched_albums
            for page in range(1, n_discogs_pages):
                fetched_albums = fetched_albums + release_search.page(page)

            # Filter out albums that doesn't actually have our artist as
            # the main artist
            fetched_albums = [
                a for a in fetched_albums if a.data.get("artist") == artist["name"]
            ]

            for fetched_album in fetched_albums:
                data = fetched_album.data
                album_id = data.get("id")

                # Check if the album already is in the database
                old_album = None
                for a in old_albums:
                    if a["album_id"] == album_id:
                        old_album = a

                if old_album is not None:
                    album_name = old_album["album_name"]
                    last_notified = Utils.sql_date_to_python_date(
                        old_album["last_notified"]
                    )
                    n_notifications = int(old_album["n_notifications"]) + 1
                    if (
                        datetime.today() - last_notified < timedelta(days=90)
                        or n_notifications < 5
                    ):
                        self.music["recent"][album_name] = (
                            "Reminder to check out the new album "
                            f"'{album_name}' by {artist['name']}."
                        )
                        Sql.update_music(
                            album_id=album_id,
                            album=album_name,
                            artist_id=old_album["artist_id"],
                            n_notifications=str(n_notifications),
                            year=old_album["year"],
                            added_date=old_album["added_date"],
                            notified_date=Utils.sql_today(),
                        )
                else:
                    album_name = data.get("title")
                    if artist["new"] == "true":
                        Sql.update_music(
                            album_id=album_id,
                            album=album_name,
                            artist_id=artist_id,
                            n_notifications="5",
                            year=data.get("year"),
                            added_date=Utils.sql_today(),
                            notified_date="1970-01-01 00:00:00",
                        )
                    else:
                        self.music["new"][
                            album_name
                        ] = f"New album '{album_name}' by {artist['name']} found!"
                        Sql.update_music(
                            album_id=album_id,
                            album=album_name,
                            artist_id=artist_id,
                            n_notifications="0",
                            year=data.get("year"),
                            added_date=Utils.sql_today(),
                            notified_date=Utils.sql_today(),
                        )

            Sql.unmark_artist_new(artist_id, artist["name"])
