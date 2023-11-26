from seasonwatch.constants import Source
from seasonwatch.exceptions import SeasonwatchException
from seasonwatch.sql import Sql


class Configure:
    """Class for modifying the shows to check."""

    @staticmethod
    def step_up_series() -> None:
        """Increase 'current season' of a TV show by 1."""
        shows = Sql.read_all_series()
        menu_data: list[dict[str, str]] = []
        for i, show in enumerate(shows):
            menu_data.append(
                {
                    "index": str(i),
                    "id": show["id"],
                    "title": show["title"],
                }
            )
        for item in menu_data:
            print(f"[{item['index']}] {item['title']}")
        selection: list[str] = input(
            "Select the shows you want to step up the current season of, separated by "
            "commas: "
        ).split(",")

        shows_to_step_up = [s["id"] for s in menu_data if s["index"] in selection]

        for show_id in shows_to_step_up:
            title = Sql.read_series(show_id).get("title")
            Sql.step_up_series(show_id)
            print(f"Successfully stepped up '{title}'.")

    @staticmethod
    def remove_series() -> None:
        """Remove a TV show."""
        shows = Sql.read_all_series()
        menu_data: list[dict[str, str]] = []
        for i, show in enumerate(shows):
            menu_data.append(
                {
                    "index": str(i),
                    "id": show["id"],
                    "title": show["title"],
                }
            )
        for item in menu_data:
            print(f"[{item['index']}] {item['title']}")
        selection: list[str] = input(
            "Select the shows you want to remove, separated by commas: "
        ).split(",")

        shows_to_remove = [s["id"] for s in menu_data if s["index"] in selection]

        for show_id in shows_to_remove:
            title = Sql.read_series(show_id).get("title")
            Sql.remove_series(show_id)
            print(f"Successfully deleted '{title}'.")

    @staticmethod
    def add_series() -> None:
        """Interactively add one or more TV-shows to the database.

        Add one or more TV-shows to the database. Requests user from
        the input and the updates the database, with default values for
        that which the user doesn't provide.
        """
        add_more = True
        while add_more:
            title = input("What the show should be called: ")
            id = input("ID of the show (after 'tv/' in the URL on TMDB): ")
            last_season = input("Last watched season: ")

            try:
                last_season_int = int(last_season)
            except ValueError:
                raise SeasonwatchException(f"Couldn't parse '{last_season}' as an int")

            print(f"title: {title}")
            print(f"TMDB ID: {id}")
            print(f"Last watched season: {last_season}")
            ok = False if input("Does this look ok? (Y/n) ") == "n" else True

            if ok:
                Sql.update_series(
                    id,
                    title,
                    last_season_int,
                    0,
                    "1970-01-01 00:00:00",
                    "1970-01-01 00:00:00",
                    Source.TMDB,
                )
            else:
                print("Data was not saved")

            print("")
            add_more = True if input("Add more shows? (y/N) ") == "y" else False
