"""Reading and writing the configuration file."""

from configparser import ConfigParser

from seasonwatch.constants import Constants

TOKENS_SECTION = "Tokens"
TMDB_TOKEN_OPTION = "tmdb_token"


def load_configuration() -> ConfigParser:
    """Return the configuration of the user.

    Creates the configuration file if it is missing, and adds an empty
    section for tokens to it if it has none, so that the user has a
    place to fill in a token by hand.
    """
    if not Constants.CONFIG_DIRECTORY.exists():
        Constants.CONFIG_DIRECTORY.mkdir(parents=True, exist_ok=True)
    if not Constants.CONFIG_PATH.exists():
        Constants.CONFIG_PATH.touch()

    configuration = ConfigParser()
    configuration.read(Constants.CONFIG_PATH)
    if not configuration.has_section(TOKENS_SECTION):
        configuration.add_section(TOKENS_SECTION)
        # Appending should preserve comments that the user has written.
        with open(Constants.CONFIG_PATH, mode="a") as config_file:
            configuration.write(config_file)
    return configuration


def read_tmdb_token(configuration: ConfigParser) -> str | None:
    """Return the TMDB token from the configuration, or None if it isn't set."""
    return configuration.get(TOKENS_SECTION, TMDB_TOKEN_OPTION, fallback=None)


def store_tmdb_token(configuration: ConfigParser, tmdb_token: str) -> None:
    """Set the TMDB token and rewrite the configuration file with it.

    Comments that the user has written in the file are lost.
    """
    configuration.set(TOKENS_SECTION, TMDB_TOKEN_OPTION, tmdb_token)
    with open(Constants.CONFIG_PATH, mode="w") as config_file:
        configuration.write(config_file)
