import toml
import os
import click
from typing import Any, Callable, Dict, List, MutableMapping
from loguru import logger
import copy
import re
import sys
import subprocess

MAX_RECURSION_DEPTH = 1000


def normalized_package_name(name: str) -> str:
    # TODO probably somewhere in poetry-core or poetry?
    # see https://www.python.org/dev/peps/pep-0426/
    return re.sub(r"[-_.]+", "-", name).lower()


def warn_after(maximum_iterations: int, warning_message: str):
    """
    Log a warning after maximum_iterations have been all consumed
    """
    counter = 0
    for counter in range(maximum_iterations + 1):
        yield counter
    if counter == maximum_iterations:
        logger.warning(warning_message)


def collect_dependencies(
    lock_toml, package_names: List[str], allow_package_filter: Callable[[str], bool]
) -> Dict[str, Any]:
    def read_lock_information(name: str):
        """select lock information for given dependency"""
        for locked_package in lock_toml["package"]:
            if locked_package["name"] == name or locked_package[
                "name"
            ] == normalized_package_name(name):
                return copy.deepcopy(locked_package)
        raise KeyError(f"Could not find '{name}' in lock file")

    collected = {
        name: read_lock_information(name)
        for name in package_names
        if allow_package_filter(name)
    }
    del package_names

    # Walk tree
    for _ in warn_after(
        MAX_RECURSION_DEPTH,
        f"Stopped looking for dependencies at a max recursion depth of {MAX_RECURSION_DEPTH}",
    ):
        dependencies_to_lock = {}
        for _, lock_information in collected.items():
            if "dependencies" in lock_information:
                # Bug here: we are only collecting a single marker, overwriting multiple mentions
                dependencies_to_lock.update(lock_information["dependencies"])
                del lock_information["dependencies"]

        # Filter dependencies we want to ignore
        dependencies_to_lock = {
            k: v for k, v in dependencies_to_lock.items() if allow_package_filter(k)
        }

        if len(dependencies_to_lock) == 0:
            break

        lock_information = {
            package_name: read_lock_information(package_name)
            for package_name in dependencies_to_lock.keys()
        }

        # merge dependencies (contains markers) and locks (contains versions)
        for package_name, dependency_attributes in dependencies_to_lock.items():
            if type(dependency_attributes) == str:
                # If this is only a version, ignore it
                dependency_attributes = {}
            del_keys(dependency_attributes, ["version"])
            lock_information[package_name].update(dependency_attributes)

        collected.update(lock_information)
    return collected


def del_keys(dictionary: Dict, keys: List[str]) -> None:
    """In-place deletion of given keys"""
    for k in keys:
        if k in dictionary:
            del dictionary[k]


def clean_dependencies(dependencies: Dict) -> Dict:
    dependencies = copy.deepcopy(dependencies)
    for _, metadata in dependencies.items():
        del_keys(metadata, ["description", "category", "name", "extras", "source"])

        if not metadata.get("optional"):
            del_keys(metadata, ["optional"])
        if "python-versions" in metadata:
            metadata["python"] = metadata["python-versions"]
            del metadata["python-versions"]
            if metadata["python"] == "*":
                del metadata["python"]

    # Collapse version to single string
    for name, metadata in dependencies.items():
        if metadata.keys() == set(["version"]):
            dependencies[name] = metadata["version"]
    return dependencies


def read_toml(filename: str) -> MutableMapping[str, Any]:
    with open(filename, "r") as project_file:
        return toml.load(project_file)


def lock_package_name(project_name: str) -> str:
    """Determine the lock project name based on the original project name"""
    separator = "_" if "_" in project_name else "-"
    return project_name + separator + "lock"


@click.command(
    help="Generate a lock package Poetry project this parent Poetry project."
)
@click.option(
    "--tests/--no-tests",
    default=False,
    show_default=True,
    help="Create a mock tests folder in the lock project or not.",
)
@click.option(
    "--wheel",
    is_flag=True,
    help="Execute poetry build wheel inside lock project.",
)
@click.option(
    "--parent/--no-parent",
    default=True,
    show_default=True,
    help="Add parent project as dependency of lock package.",
)
@click.option(
    "--ignore",
    metavar="REGEX",
    multiple=True,
    help="Ignore packages that fully match the given re.Pattern regular expression.",
)
def main(tests: bool, wheel: bool, parent: bool, ignore: List[str]):

    logger.remove()
    logger.add(sys.stdout, colorize=True, format="<level>{level}</level> {message}")

    ignore_patterns = [re.compile(ignore_pattern) for ignore_pattern in ignore]

    def allow_package_filter(package_name: str) -> bool:
        return all(
            [pattern.fullmatch(package_name) is None for pattern in ignore_patterns]
        )

    run(
        should_create_tests=tests,
        run_poetry_build_wheel=wheel,
        allow_package_filter=allow_package_filter,
        add_parent=parent,
    )


def project_root_dependencies(project: MutableMapping[str, Any]) -> List[str]:
    """
    Package names of project dependencies described in the pyproject.toml
    """
    return [
        k for k in project["tool"]["poetry"]["dependencies"].keys() if k != "python"
    ]


def run(
    should_create_tests: bool,
    run_poetry_build_wheel: bool,
    allow_package_filter: Callable[[str], bool],
    add_parent: bool,
) -> None:
    project = read_toml("pyproject.toml")
    lock = read_toml("poetry.lock")

    root_dependencies = project_root_dependencies(project)
    dependencies = clean_dependencies(
        collect_dependencies(lock, root_dependencies, allow_package_filter)
    )
    dependencies["python"] = project["tool"]["poetry"]["dependencies"]["python"]
    if add_parent:
        dependencies[
            normalized_package_name(project["tool"]["poetry"]["name"])
        ] = project["tool"]["poetry"]["version"]
    project["tool"]["poetry"]["name"] = lock_package_name(
        project["tool"]["poetry"]["name"]
    )
    project["tool"]["poetry"]["description"] = (
        project["tool"]["poetry"]["description"] + " lock package"
    ).strip()
    project["tool"]["poetry"]["dependencies"] = dependencies

    del_keys(
        project["tool"]["poetry"], ["scripts", "readme", "include", "extras", "plugins"]
    )

    lock_project_path = create_or_update(project, should_create_tests)
    if run_poetry_build_wheel:
        os.chdir(lock_project_path)
        subprocess.check_call(["poetry", "build", "--format", "wheel"])


def create_or_update(project, should_create_tests: bool) -> str:
    lock_project_path = project["tool"]["poetry"]["name"]
    logger.info(f"Writing {lock_project_path}")

    # Create module folder
    module_path = os.path.join(
        lock_project_path,
        project["tool"]["poetry"]["name"].replace("-", "_"),
    )
    os.makedirs(module_path, exist_ok=True)
    module_init = os.path.join(module_path, "__init__.py")
    create_and_write(
        module_init, '__version__ = "{}"\n'.format(project["tool"]["poetry"]["version"])
    )

    # Create tests folder
    if should_create_tests:
        create_tests(lock_project_path)

    # Create project toml
    with open(
        os.path.join(lock_project_path, "pyproject.toml"), "w"
    ) as requirements_toml:
        toml.dump(project, requirements_toml)
    return lock_project_path


def create_and_write(path, contents):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as output_file:
            output_file.write(contents)


def create_tests(lock_project_path):
    tests_path = os.path.join(lock_project_path, "tests")
    tests_init_path = os.path.join(tests_path, "__init__.py")

    create_and_write(tests_init_path, "")

    tests_mock = os.path.join(tests_path, "test_nothing.py")
    create_and_write(tests_mock, "def test_nothing():\n    pass\n")


if __name__ == "__main__":
    main()
