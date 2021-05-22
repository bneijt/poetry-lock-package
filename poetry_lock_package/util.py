import os
import re
from contextlib import contextmanager
from typing import Callable, Dict, List

from tomlkit import loads
from tomlkit.toml_document import TOMLDocument


def after(maximum_iterations: int, at_end_of_iteration: Callable[[], None]):
    """
    Log a warning after maximum_iterations have been all consumed
    """
    counter = 0
    for counter in range(maximum_iterations):
        yield counter
    if counter == maximum_iterations - 1:
        at_end_of_iteration()


def normalized_package_name(name: str) -> str:
    # TODO probably somewhere in poetry-core or poetry?
    # see https://www.python.org/dev/peps/pep-0426/
    return re.sub(r"[-_.]+", "-", name).lower()


def del_keys(dictionary: TOMLDocument, keys: List[str]) -> None:
    """In-place deletion of given keys"""
    for k in keys:
        if k in dictionary:
            del dictionary[k]


def read_toml(filename: str) -> TOMLDocument:
    with open(filename, "r", encoding="utf-8") as project_file:
        return loads(project_file.read())


def create_and_write(path, contents):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as output_file:
            output_file.write(contents)


@contextmanager
def changed_directory(new_path: str):
    old_path = os.getcwd()
    try:
        os.chdir(new_path)
        yield new_path
    finally:
        os.chdir(old_path)
