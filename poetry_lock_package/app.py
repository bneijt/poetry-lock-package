from cleo.application import Application
from cleo.commands.command import Command
from .lib import run
from . import __version__
import re


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a lock package Poetry project this parent Poetry project."
    )
    parser.add_argument(
        "--tests",
        help="Create a mock tests folder in the lock project or not.",
        action="store_true",
    )
    parser.add_argument(
        "--wheel",
        help="Execute poetry build wheel inside lock project.",
        action="store_true",
    )
    parser.add_argument(
        "--move",
        help="Move poetry lock package dist/ files to local dist folder.",
        action="store_true",
    )
    parser.add_argument(
        "--clean", help="Remove lock project afterwards.", action="store_true"
    )
    parser.add_argument(
        "--build", help="Alias for --wheel --move --clean.", action="store_true"
    )
    parser.add_argument(
        "--no-root",
        help="Do not add the root/parent project as a dependency of lock package.",
        action="store_true",
    )
    parser.add_argument(
        "--ignore",
        metavar="REGEX",
        help="Do not add the root/parent project as a dependency of lock package.",
        action="append",
        default=[],
    )

    return parser.parse_args()


application = Application(name="poetry-lock-package", version=__version__)
application.add(LockCommand().default())


def main():
    application.run()


if __name__ == "__main__":
    main()
