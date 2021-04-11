from poetry_lock_package.app import (
    run,
    lock_package_name,
    clean_dependencies,
    collect_dependencies,
)
import shutil
import toml


def test_main():
    try:
        run(True)
    finally:
        shutil.rmtree("poetry-lock-package-lock", ignore_errors=True)


def test_lock_package_name():
    assert lock_package_name("a") == "a-lock"
    assert lock_package_name("a-b") == "a-b-lock"
    assert lock_package_name("a_b") == "a_b_lock"


def test_collect_dependencies():
    with open("tests/resources/example1.lock", "r") as lock_file:
        lock_toml = toml.load(lock_file)
        assert clean_dependencies(
            collect_dependencies(lock_toml, ["atomicwrites"])
        ) == {
            "atomicwrites": {
                "python": ">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*",
                "version": "1.4.0",
            }
        }

        assert clean_dependencies(collect_dependencies(lock_toml, ["loguru"]))[
            "win32-setctime"
        ] == {
            "markers": 'sys_platform == "win32"',
            "python": ">=3.5",
            "version": "1.0.3",
        }
