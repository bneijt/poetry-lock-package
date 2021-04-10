from poetry_lock_package.app import run, lock_package_name
import shutil


def test_main():
    try:
        run(True)
    finally:
        shutil.rmtree("poetry-lock-package-lock")


def test_lock_package_name():
    assert lock_package_name("a") == "a-lock"
    assert lock_package_name("a-b") == "a-b-lock"
    assert lock_package_name("a_b") == "a_b_lock"
