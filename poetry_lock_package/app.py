from cleo.application import Application
from . import __version__
from .plugin import BuildLockCommand
import sys


def main() -> int:
    application = Application(name="poetry-lock-package", version=__version__)
    application.add(BuildLockCommand())
    return application.run()


if __name__ == "__main__":
    sys.exit(main())
