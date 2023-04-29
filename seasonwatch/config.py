from seasonwatch.exceptions import SeasonwatchException
from seasonwatch.sql import Sql


class Configure:
    @staticmethod
    def series() -> None:
        """
        Function for adding TV-shows to the database. Requests user from
        the input and the updates the database, with default values for
        that which the user doesn't provide.
        """
        add_more = True
        while add_more:
            title = input("Title of the show: ")
            id = input("ID of the show (after 'tt' in the url on IMDB): ")
            last_season = input("Last watched season: ")

            try:
                last_season_int = int(last_season)
            except ValueError:
                raise SeasonwatchException(f"Couldn't parse '{last_season}' as an int")

            print(f"title: {title}")
            print(f"ID: {id}")
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
                )
            else:
                print("Data was not saved")

            print("")
            add_more = True if input("Add more shows? (y/N) ") == "y" else False
