class SeasonwatchException(Exception):
    """
    This exception can be inherited from for Seasonwatch specific custom
    exception of raised independently for exceptions that should be
    handled internally and will then be logged with the exception
    message if it is raised.
    """


class ConfigException(SeasonwatchException):
    """
    Raised when the configuration cannot be parsed
    """
