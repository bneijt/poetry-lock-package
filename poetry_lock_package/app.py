import toml
import os
import click
from loguru import logger


def dependency_spec(lock_information, dependency_name):
    dependency_information = next(
        filter(lambda x: x["name"] == dependency_name, lock_information["package"])
    )

    attributes = ["version", "python", "markers"]
    spec = {}
    for attr in attributes:
        attr_value = dependency_information.get(attr)
        if attr_value and attr_value != "*":
            spec[attr] = attr_value
    if list(spec.keys()) == ["version"]:
        return spec["version"]
    return spec


def read_lock_versions_for(direct_dependencies):
    with open("poetry.lock", "r") as lock_file:
        lock_toml = toml.load(lock_file)

        dependencies = {
            dependency_name: dependency_spec(lock_toml, dependency_name)
            for dependency_name in direct_dependencies
        }
        return dependencies


def read_project():
    with open("pyproject.toml", "r") as project_file:
        project_toml = toml.load(project_file)
        return project_toml


def lock_package_name(project_name: str) -> str:
    """Determine the lock project name based on the original project name"""
    separator = "_" if "_" in project_name else "-"
    return project_name + separator + "lock"


@click.command(help="Generate a poetry lock package project from a poetry project")
@click.option("--tests/--no-tests", default=True)
def main(tests):
    run(should_create_tests=tests)
    logger.info("Done")


def run(should_create_tests: bool) -> None:
    project = read_project()
    dependencies = read_lock_versions_for(
        [k for k in project["tool"]["poetry"]["dependencies"].keys() if k != "python"]
    )
    dependencies["python"] = project["tool"]["poetry"]["dependencies"]["python"]
    project["tool"]["poetry"]["name"] = lock_package_name(
        project["tool"]["poetry"]["name"]
    )
    project["tool"]["poetry"]["description"] = (
        project["tool"]["poetry"]["description"] + " lock package"
    ).strip()
    project["tool"]["poetry"]["dependencies"] = dependencies

    create_or_update(project, should_create_tests)


def create_or_update(project, should_create_tests: bool):
    lock_project_path = project["tool"]["poetry"]["name"]

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
    return


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
