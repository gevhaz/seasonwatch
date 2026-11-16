from seasonwatch.exceptions import SeasonwatchException
from seasonwatch.series import Series
from seasonwatch.sql import Sql


class Configure:
    """Class for modifying the shows to check."""

    @staticmethod
    def step_up_series() -> None:
        """Increase 'current season' of a TV show by 1."""
        all_series = Sql.read_all_series()
        for index, series in enumerate(all_series):
            print(f"[{index}] {series.title}")
        selection: list[str] = input(
            "Select the shows you want to step up the current season of, separated by "
            "commas: "
        ).split(",")

        for index, series in enumerate(all_series):
            if str(index) not in selection:
                continue
            Sql.step_up_series(series.tmdb_id)
            print(f"Successfully stepped up '{series.title}'.")

    @staticmethod
    def remove_series() -> None:
        """Remove a TV show."""
        all_series = Sql.read_all_series()
        for index, series in enumerate(all_series):
            print(f"[{index}] {series.title}")
        selection: list[str] = input(
            "Select the shows you want to remove, separated by commas: "
        ).split(",")

        for index, series in enumerate(all_series):
            if str(index) not in selection:
                continue
            Sql.remove_series(series.tmdb_id)
            print(f"Successfully deleted '{series.title}'.")

    @staticmethod
    def add_series() -> None:
        """Interactively add one or more TV-shows to the database.

        Asks the user for the title, the TMDB ID and the last watched
        season of each show, and for confirmation before storing it.

        :raises SeasonwatchException: If the ID or the season that the
            user enters isn't a number.
        """
        add_more = True
        while add_more:
            title = input("What the show should be called: ")
            tmdb_id_text = input("ID of the show (after 'tv/' in the URL on TMDB): ")
            last_season_text = input("Last watched season: ")

            try:
                tmdb_id = int(tmdb_id_text)
            except ValueError:
                raise SeasonwatchException(
                    f"Couldn't parse '{tmdb_id_text}' as a TMDB ID. It is the "
                    "number after 'tv/' in the URL, without the name after it."
                )
            try:
                last_watched_season = int(last_season_text)
            except ValueError:
                raise SeasonwatchException(
                    f"Couldn't parse '{last_season_text}' as an int"
                )

            print(f"title: {title}")
            print(f"TMDB ID: {tmdb_id}")
            print(f"Last watched season: {last_watched_season}")
            ok = False if input("Does this look ok? (Y/n) ") == "n" else True

            if ok:
                Sql.add_series(
                    Series(
                        tmdb_id=tmdb_id,
                        title=title,
                        last_watched_season=last_watched_season,
                    )
                )
            else:
                print("Data was not saved")

            print("")
            add_more = True if input("Add more shows? (y/N) ") == "y" else False
