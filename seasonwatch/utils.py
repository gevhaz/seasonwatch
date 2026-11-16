from datetime import date, datetime

from seasonwatch.exceptions import SeasonwatchException


class Utils:
    """
    Collection of utilities functions that are generally useful
    """

    @staticmethod
    def timestamp() -> str:
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    @staticmethod
    def sql_today() -> str:
        """Get today's date in format used by SQLite."""
        return date.today().strftime("%Y-%m-%d 00:00:00")

    @staticmethod
    def sql_date_to_python_date(sql_date: str) -> datetime:
        try:
            python_date = datetime.strptime(sql_date, "%Y-%m-%d 00:00:00")
        except ValueError:
            raise SeasonwatchException(f"Couldn't parse '{sql_date}' as date.")
        return python_date
