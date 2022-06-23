from typing import Any

import yaml

from seasonwatch.exceptions import ConfigException


class ConfigParser:
    """
    Class to parse and store the configuration of what media to check
    for news about and how to find the media.
    """

    def __init__(self) -> None:
        self.series: list[dict[str, str]] = []
        self.movies: list[dict[str, str]] = []

    @staticmethod
    def string_or_int(value: Any) -> str:
        """
        :param value: The value to be vaildated.

        :raises:ConfigException: Raised if the value is neither string nor int.

        :return: The original value as a string if validation passes
        """
        if isinstance(value, int):
            value = str(value)

        if not isinstance(value, str):
            raise ConfigException(
                f"Value should be string or int but {type(value)} was found"
            )

        return value

    def parse_config(self, file_path: str) -> None:
        """
        Pase the config at the specied location.

        :param file_path: Path to the config.
        """
        with open(file_path, "r") as f:
            config: Any = yaml.safe_load(f)

        if not isinstance(config, dict):
            raise ConfigException("The configuration cannot be parsed as a dictionary")

        all_series = config.get("series")
        if all_series is not None:
            for series in all_series:

                try:
                    title = ConfigParser.string_or_int(series.get("title"))
                except ConfigException as e:
                    raise ConfigException(f"Title: {e}")

                try:
                    id = ConfigParser.string_or_int(series.get("id"))
                except ConfigException as e:
                    raise ConfigException(f"{title}: {e}")

                try:
                    last_season = ConfigParser.string_or_int(
                        series.get("current_season")
                    )
                except ConfigException as e:
                    raise ConfigException(f"{title}: {e}")

                self.series.append(
                    {
                        "title": title,
                        "id": id,
                        "current_season": last_season,
                    }
                )

        movies = config.get("movies")
        if movies is not None:
            for movie in movies:

                try:
                    title = ConfigParser.string_or_int(movie.get("title"))
                except ConfigException as e:
                    raise ConfigException(f"Title: {e}")

                try:
                    id = ConfigParser.string_or_int(movie.get("id"))
                except ConfigException as e:
                    raise ConfigException(f"{title}: {e}")

                self.movies.append(
                    {
                        "title": title,
                        "id": id,
                    }
                )
