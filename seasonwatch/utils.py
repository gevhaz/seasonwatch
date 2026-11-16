from datetime import datetime


class Utils:
    """
    Collection of utilities functions that are generally useful
    """

    @staticmethod
    def timestamp() -> str:
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
