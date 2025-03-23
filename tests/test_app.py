import os
from typing import Callable

import toml

from poetry_lock_package.app import (
    clean_dependencies,
    collect_dependencies,
    lock_package_name,
    project_root_dependencies,
    run,
)
from poetry_lock_package.util import read_toml


def always(result: bool) -> Callable[[str], bool]:
    def impl(_: str) -> bool:
        return result

    return impl


def test_main():
    run(
        should_create_tests=False,
        run_poetry_build_wheel=False,
        move_package_after_build=False,
        clean_up_project=True,
        allow_package_filter=lambda _: True,
        add_root=True,
    )
    assert not os.path.exists("poetry-lock-package-lock"), (
        "Should have been removed by clean"
    )


def test_lock_package_name():
    assert lock_package_name("a") == "a-lock"
    assert lock_package_name("a-b") == "a-b-lock"
    assert lock_package_name("a_b") == "a_b_lock"


def test_collect_dependencies():
    with open("tests/resources/example1.lock", "r", encoding="utf-8") as lock_file:
        lock_toml = toml.load(lock_file)
        assert clean_dependencies(
            collect_dependencies(lock_toml, ["atomicwrites"], always(True))
        ) == {
            "atomicwrites": {
                "python": ">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*",
                "version": "1.4.0",
            }
        }

        assert clean_dependencies(
            collect_dependencies(lock_toml, ["loguru"], always(True))
        )["win32-setctime"] == {
            "markers": 'sys_platform == "win32"',
            "python": ">=3.5",
            "version": "1.0.3",
        }


def test_lock_file_v2() -> None:
    with open("tests/resources/poetry_v2.lock", "r", encoding="utf-8") as lock_file:
        lock_toml = toml.load(lock_file)
        assert clean_dependencies(
            collect_dependencies(lock_toml, ["arrow"], always(True))
        ) == {
            "arrow": {"python": ">=3.6", "version": "1.2.3"},
            "python-dateutil": {
                "python": "!=3.0.*,!=3.1.*,!=3.2.*,>=2.7",
                "version": "2.8.2",
            },
            "six": {"python": ">=2.7, !=3.0.*, !=3.1.*, !=3.2.*", "version": "1.16.0"},
        }


def test_pybluez_git_reference():
    lock_toml = read_toml("tests/resources/pybluez_git.lock")
    project_toml = read_toml("tests/resources/pybluez_git.toml")
    root_dependencies = project_root_dependencies(project_toml)

    assert clean_dependencies(
        collect_dependencies(lock_toml, root_dependencies, always(True))
    ) == {
        "PyBluez": {
            "python": ">=3.5",
            "version": "0.30",
        }
    }


def test_project_root_dependencies() -> None:
    project = read_toml("pyproject.toml")

    root_deps = project_root_dependencies(project)

    assert root_deps, "Should find root dependencies"
    assert "python" not in root_deps, "Should ignore python"


def test_clean_dependencies_should_ignore_extra_via_dependency():
    """
    The lock contains a reference to a dependency with an extra in it, but also
    the main package without extra reference. This should end up with the root dependency without the extra
    on it.
    """
    lock_toml = read_toml("tests/resources/extras_example.lock")

    dependencies = clean_dependencies(
        collect_dependencies(lock_toml, ["boto3", "smart-open"], lambda x: True)
    )
    assert "markers" not in dependencies["boto3"], "Should not have any markers set"


def test_issue_36_lock() -> None:
    """If the dependency information contains more markers for different versions, we incorrectly merge the configuration"""
    with open("tests/resources/issue_36.lock", "r", encoding="utf-8") as lock_file:
        lock_toml = toml.load(lock_file)
        collected_deps = collect_dependencies(
            lock_toml, ["aioboto3", "docker", "requests"], always(True)
        )
        cleaned_deps = clean_dependencies(collected_deps)
        assert cleaned_deps["urllib3"]["version"] == "1.26.18"
