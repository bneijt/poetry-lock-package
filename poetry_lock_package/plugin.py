from cleo.commands.command import Command
from poetry.plugins.application_plugin import ApplicationPlugin


class BuildLockCommand(Command):

    name = "build-lock"

    def handle(self) -> int:
        self.line("My command")

        return 0


def factory():
    return BuildLockCommand()


class BuildLockApplicationPlugin(ApplicationPlugin):
    def activate(self, application):
        application.command_loader.register_factory(BuildLockCommand.name, factory)
