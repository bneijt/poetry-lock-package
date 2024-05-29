from contextlib import contextmanager
import os
from pathlib import Path
from typing import Iterator
from cleo.testers.command_tester import CommandTester
from cleo.io.outputs.output import Verbosity


@contextmanager
def as_cwd(path: Path) -> Iterator[Path]:
    old_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield path
    finally:
        os.chdir(old_cwd)


def test_build_command_will_execute_plugin(tester: CommandTester) -> None:
    with as_cwd("tests/resources/simply_complete"):
        tester.execute(verbosity=Verbosity.DEBUG)
