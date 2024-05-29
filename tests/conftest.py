from __future__ import annotations

from pathlib import Path
from typing import Protocol

import pytest

from cleo.io.null_io import NullIO
from cleo.testers.command_tester import CommandTester
from poetry.installation import Installer
from poetry.utils.env import MockEnv


from poetry.installation.executor import Executor
from poetry.poetry import Poetry
from poetry.utils.env import Env

from poetry.console.application import Application
from poetry.factory import Factory


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
    ) -> CommandTester: ...


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
        assert cmd, "Should have found build command"
        tester = CommandTester(cmd)

        if poetry:
            app._poetry = poetry

        poetry = app.poetry

        return tester

    return _tester


@pytest.fixture
def poetry() -> Poetry:
    return Factory().create_poetry()


@pytest.fixture
def tester(
    command_tester_factory: CommandTesterFactory, poetry: Poetry
) -> CommandTester:
    return command_tester_factory(poetry=poetry)
