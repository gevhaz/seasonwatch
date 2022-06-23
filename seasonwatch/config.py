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

    def parse_config(self, file_path: str):
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
                title: Any = series.get("title")
                id: Any = series.get("id")
                last_season: Any = series.get("current_season")

                if isinstance(title, int):
                    title = str(title)

                if isinstance(id, int):
                    id = str(id)

                if isinstance(last_season, int):
                    last_season = str(last_season)

                if not isinstance(title, str):
                    raise ConfigException(
                        f"title should be string or int but {type(title)} was found"
                    )

                if not isinstance(id, str):
                    raise ConfigException(
                        f"id should be string or int but {type(id)} was found for "
                        f"show: {title}"
                    )

                if not isinstance(last_season, str):
                    raise ConfigException(
                        "current_season should be string or int but "
                        f"{type(last_season)} was found {title}"
                    )

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
                title: Any = movie.get("title")
                id: Any = movie.get("id")
                last_season: Any = movie.get("current_season")

                if isinstance(title, int):
                    title = str(title)

                if isinstance(id, int):
                    id = str(id)

                if not isinstance(title, str):
                    raise ConfigException(
                        f"title should be string or int but {type(title)} was found"
                    )

                if not isinstance(id, str):
                    raise ConfigException(
                        f"id should be string or int but {type(id)} was found for "
                        f"show: {title}"
                    )

                self.movies.append(
                    {
                        "title": title,
                        "id": id,
                    }
                )
