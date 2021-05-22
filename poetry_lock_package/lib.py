import copy
import os
import shutil
import subprocess
from typing import Any, Callable, Dict, List, MutableMapping
from cleo.io.io import IO

from tomlkit.toml_document import TOMLDocument


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
    io: IO,
    lock_toml,
    package_names: List[str],
    allow_package_filter: Callable[[str], bool],
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
        lambda: io.write_line(
            f"<error>Stopped looking for dependencies at a max recursion depth of {MAX_RECURSION_DEPTH}</error>"
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


def project_root_dependencies(project: MutableMapping[str, Any]) -> List[str]:
    """
    Package names of project dependencies described in the pyproject.toml
    """
    return [
        k for k in project["tool"]["poetry"]["dependencies"].keys() if k != "python"
    ]


def run(
    io: IO,
    run_poetry_build_wheel: bool,
    move_package_after_build: bool,
    clean_up_project: bool,
    allow_package_filter: Callable[[str], bool],
    add_root: bool,
) -> int:
    project = read_toml("pyproject.toml")
    lock = read_toml("poetry.lock")

    root_dependencies = project_root_dependencies(project)
    dependencies = clean_dependencies(
        collect_dependencies(io, lock, root_dependencies, allow_package_filter)
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
        project["tool"]["poetry"],
        ["scripts", "readme", "include", "extras", "plugins", "packages"],
    )

    lock_project_path = create_or_update(io, project)
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

    return 0


def create_or_update(io: IO, project: TOMLDocument) -> str:
    lock_project_path = project["tool"]["poetry"]["name"]
    io.write_line(f"Writing {lock_project_path}")

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

    # Create project toml
    with open(
        os.path.join(lock_project_path, "pyproject.toml"), "w", encoding="utf-8"
    ) as requirements_toml:
        requirements_toml.write(project.as_string())
    return lock_project_path
