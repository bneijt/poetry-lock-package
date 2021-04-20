from typing import Counter

from poetry_lock_package.util import after, normalized_package_name


def test_normalized_package_name():
    assert normalized_package_name("a") == "a"
    assert normalized_package_name("a-b") == "a-b"
    assert normalized_package_name("a_b") == "a-b"


def test_after():
    counter = 0

    def inc_counter():
        nonlocal counter
        print("increment counter")
        counter += 1

    assert counter == 0
    after(0, inc_counter)
    assert counter == 0
    list(after(0, inc_counter))
    assert counter == 0, "Still no reason to call"
    a = list(after(1, inc_counter))
    assert counter == 1, "Should be called because we reached end of list"
