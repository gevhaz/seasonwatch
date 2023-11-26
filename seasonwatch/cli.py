from argparse import ArgumentParser, Namespace


class Cli:
    @staticmethod
    def parse() -> Namespace:
        """
        Parse the arguments given on command line.
        """
        parser = ArgumentParser(prog="Seasonwatch")

        subparsers = parser.add_subparsers(dest="subparser_name")

        tv = subparsers.add_parser(
            "tv",
            help="Subcommand for working with TV shows",
        )

        subparsers.add_parser(
            "configure",
            help="Configure Seasonwatch for use",
        )

        tv.add_argument(
            "-r",
            "--remove",
            help="Interactively remove a TV show",
            action="store_true",
            dest="remove",
            required=False,
        )

        tv.add_argument(
            "-s",
            "--step-up",
            help="Step up last watched season number of TV shows",
            action="store_true",
            dest="step_up",
            required=False,
        )

        tv.add_argument(
            "-a",
            "--add",
            help="Add tv-shows",
            action="store_true",
            dest="add",
            required=False,
        )

        tv.add_argument(
            "-l",
            "--list",
            help="List stored tv-shows",
            action="store_true",
            dest="list_shows",
            required=False,
        )

        return parser.parse_args()
