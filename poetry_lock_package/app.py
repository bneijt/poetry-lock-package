import copy
import os
import re
import shutil
import subprocess
from typing import Any, Callable, Dict, List, MutableMapping
import logging
import toml
import argparse

from poetry_lock_package.util import (
    after,
    changed_directory,
    create_and_write,
    del_keys,
    normalized_package_name,
    read_toml,
)

MAX_RECURSION_DEPTH = 1000


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
    for _ in after(
        MAX_RECURSION_DEPTH,
        lambda: logging.error(
            f"Stopped looking for dependencies at a max recursion depth of {MAX_RECURSION_DEPTH}"
        ),
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


def lock_package_name(project_name: str) -> str:
    """Determine the lock project name based on the original project name"""
    separator = "_" if "_" in project_name else "-"
    return project_name + separator + "lock"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a lock package Poetry project this parent Poetry project."
    )
    parser.add_argument(
        "--tests",
        help="Create a mock tests folder in the lock project or not.",
        action="store_true",
    )
    parser.add_argument(
        "--wheel",
        help="Execute poetry build wheel inside lock project.",
        action="store_true",
    )
    parser.add_argument(
        "--move",
        help="Move poetry lock package dist/ files to local dist folder.",
        action="store_true",
    )
    parser.add_argument(
        "--clean", help="Remove lock project afterwards.", action="store_true"
    )
    parser.add_argument(
        "--build", help="Alias for --wheel --move --clean.", action="store_true"
    )
    parser.add_argument(
        "--no-root",
        help="Do not add the root/parent project as a dependency of lock package.",
        action="store_true",
    )
    parser.add_argument(
        "--ignore",
        metavar="REGEX",
        help="Do not add the root/parent project as a dependency of lock package.",
        action="append",
        default=[],
    )

    return parser.parse_args()


def main():
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

    args = parse_arguments()

    wheel = args.wheel
    move = args.move
    clean = args.clean
    ignore = args.ignore

    ignore_patterns = [re.compile(ignore_pattern) for ignore_pattern in ignore]

    def allow_package_filter(package_name: str) -> bool:
        return all(
            [pattern.fullmatch(package_name) is None for pattern in ignore_patterns]
        )

    if args.build:
        wheel = True
        move = True
        clean = True

    run(
        should_create_tests=args.tests,
        run_poetry_build_wheel=wheel,
        move_package_after_build=move,
        clean_up_project=clean,
        allow_package_filter=allow_package_filter,
        add_root=not args.no_root,
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
    move_package_after_build: bool,
    clean_up_project: bool,
    allow_package_filter: Callable[[str], bool],
    add_root: bool,
) -> None:
    project = read_toml("pyproject.toml")
    lock = read_toml("poetry.lock")

    root_dependencies = project_root_dependencies(project)
    dependencies = clean_dependencies(
        collect_dependencies(lock, root_dependencies, allow_package_filter)
    )
    dependencies["python"] = project["tool"]["poetry"]["dependencies"]["python"]
    if add_root:
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
        with changed_directory(lock_project_path):
            subprocess.check_call(["poetry", "build", "--format", "wheel"])

    if move_package_after_build:
        if not os.path.exists("dist"):
            os.mkdir("dist")
        for dist_filename in os.listdir(os.path.join(lock_project_path, "dist")):
            shutil.move(
                os.path.join(lock_project_path, "dist", dist_filename),
                os.path.join("dist", dist_filename),
            )

    if clean_up_project:
        shutil.rmtree(lock_project_path)


def create_or_update(project, should_create_tests: bool) -> str:
    lock_project_path = project["tool"]["poetry"]["name"]
    logging.info(f"Writing {lock_project_path}")

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


def create_tests(lock_project_path: str) -> None:
    """
    Create a mock tests directory

    If you have a default build-test-publish CI pipeline
    and you require tests on the lock package
    """
    tests_path = os.path.join(lock_project_path, "tests")
    tests_init_path = os.path.join(tests_path, "__init__.py")

    create_and_write(tests_init_path, "")

    tests_mock = os.path.join(tests_path, "test_nothing.py")
    create_and_write(tests_mock, "def test_nothing():\n    pass\n")


if __name__ == "__main__":
    main()
