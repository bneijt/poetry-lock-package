from cleo.application import Application
from cleo.commands.command import Command
from .lib import run
from . import __version__
import re


class LockCommand(Command):
    """
    Generate a lock package Poetry project this root Poetry project.

    lock
        {--wheel : Execute poetry build wheel inside lock project.}
        {--move : Move poetry lock package dist/ files to local dist folder.}
        {--clean : Remove lock project afterwards.}
        {--build : Alias for --wheel --move --clean.}
        {--no-root : Do not add root as a dependency of lock package}
        {--ignore=* : Ignore packages that fully match the given re.Pattern regular expression.}
    """

    def handle(self):
        ignore_patterns = [
            re.compile(ignore_pattern) for ignore_pattern in self.option("ignore")
        ]

        def allow_package_filter(package_name: str) -> bool:
            return all(
                [pattern.fullmatch(package_name) is None for pattern in ignore_patterns]
            )

        wheel = self.option("wheel")
        move = self.option("move")
        clean = self.option("clean")
        if self.option("build"):
            wheel = True
            move = True
            clean = True

        run(
            self.io,
            run_poetry_build_wheel=wheel,
            move_package_after_build=move,
            clean_up_project=clean,
            allow_package_filter=allow_package_filter,
            add_root=not self.option("no-root"),
        )


application = Application(name="poetry-lock-package", version=__version__)
application.add(LockCommand().default())


def main():
    application.run()


if __name__ == "__main__":
    main()
