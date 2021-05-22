from cleo.commands.command import Command
from poetry.plugins.application_plugin import ApplicationPlugin
import re
from .lib import run


class BuildLockCommand(Command):
    """
    Build a lock package for this project.

    build-lock
        {--no-root : Do not add root, this project, as a dependency of lock package}
        {--ignore=* : Ignore packages that fully match the given re.Pattern regular expression.}
    """

    name = "build-lock"

    def handle(self) -> int:
        ignore_patterns = []
        # TODO
        # ignore_patterns = [
        #     re.compile(ignore_pattern) for ignore_pattern in self.option("ignore")
        # ]
        # TODO
        # add_root = not self.option("no-root")
        add_root = True

        def allow_package_filter(package_name: str) -> bool:
            return all(
                [pattern.fullmatch(package_name) is None for pattern in ignore_patterns]
            )

        return run(
            self.io,
            run_poetry_build_wheel=True,
            move_package_after_build=True,
            clean_up_project=True,
            allow_package_filter=allow_package_filter,
            add_root=add_root,
        )


def factory():
    return BuildLockCommand()


class BuildLockApplicationPlugin(ApplicationPlugin):
    def activate(self, application):
        application.command_loader.register_factory(BuildLockCommand.name, factory)
