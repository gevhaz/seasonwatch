from argparse import ArgumentParser, Namespace


class Cli:
    @staticmethod
    def parse() -> Namespace:
        """
        Parse the arguments given on command line.
        """
        parser = ArgumentParser(prog="Seasonwatch")

        subparsers = parser.add_subparsers(dest="subparser_name")

        configure = subparsers.add_parser(
            "configure",
            help="Configure seasonwatch with new TV shows, movies or music",
        )

        configure.add_argument(
            "-t",
            "--tv-shows",
            help="Add tv-shows",
            action="store_true",
            dest="series",
            required=False,
        )

        return parser.parse_args()
