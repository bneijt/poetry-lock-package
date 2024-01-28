from __future__ import annotations

from typing import Protocol

import pytest

from cleo.io.null_io import NullIO
from cleo.testers.command_tester import CommandTester
from poetry.console.commands.env_command import EnvCommand
from poetry.console.commands.build import BuildCommand
from poetry.console.commands.installer_command import InstallerCommand
from poetry.installation import Installer
from poetry.utils.env import MockEnv


from poetry.installation.executor import Executor
from poetry.poetry import Poetry
from poetry.utils.env import Env

from poetry.console.application import Application
from poetry.factory import Factory
from poetry.installation.executor import Executor
from poetry.packages import Locker


class PoetryTestApplication(Application):
    def __init__(self, poetry: Poetry) -> None:
        super().__init__()
        self._poetry = poetry


@pytest.fixture
def app(poetry: Poetry) -> PoetryTestApplication:
    app_ = PoetryTestApplication(poetry)
    return app_


class CommandTesterFactory(Protocol):
    def __call__(
        self,
        command: str,
        poetry: Poetry | None = None,
        installer: Installer | None = None,
        executor: Executor | None = None,
        environment: Env | None = None,
    ) -> CommandTester:
        ...


@pytest.fixture
def env(tmp_path: Path) -> MockEnv:
    path = tmp_path / ".venv"
    path.mkdir(parents=True)
    return MockEnv(path=path, is_venv=True)


@pytest.fixture
def command_tester_factory(
    app: PoetryTestApplication, env: MockEnv
) -> CommandTesterFactory:
    def _tester(
        poetry: Poetry | None = None,
    ) -> CommandTester:
        app._load_plugins(NullIO())
        cmd = app.find("build")
        cmd.set_env(env)
        tester = CommandTester(cmd)

        # Setting the formatter from the application
        # TODO: Find a better way to do this in Cleo
        app_io = app.create_io()
        formatter = app_io.output.formatter
        tester.io.output.set_formatter(formatter)
        tester.io.error_output.set_formatter(formatter)

        if poetry:
            app._poetry = poetry

        poetry = app.poetry

        return tester

    return _tester


@pytest.fixture
def poetry() -> Poetry:
    return Factory().create_poetry("tests/resources/simply_complete")


@pytest.fixture
def tester(
    command_tester_factory: CommandTesterFactory, poetry: Poetry
) -> CommandTester:
    return command_tester_factory(poetry=poetry)
