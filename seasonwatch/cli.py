from argparse import SUPPRESS, ArgumentParser, Namespace


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
            help="Change set of saved TV shows",
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
            help=SUPPRESS,
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

        return parser.parse_args()
