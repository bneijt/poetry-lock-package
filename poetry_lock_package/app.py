import toml
import os
import click


def read_lock_versions():
    with open("poetry.lock", "r") as lock_file:
        lock_toml = toml.load(lock_file)
        return {
            p["name"]: p["version"]
            for p in lock_toml["package"]
            if p["category"] == "dev" and not p["optional"]
        }


def read_project():
    with open("pyproject.toml", "r") as project_file:
        project_toml = toml.load(project_file)
        return project_toml


def lock_package_name(project_name: str) -> str:
    """Determine the lock project name based on the original project name"""
    separator = "_" if "_" in project_name else "-"
    return project_name + separator + "lock"


@click.command(help="Generate a poetry lock package project from a poetry project")
def main():
    run()


def run():
    project = read_project()
    dependencies = read_lock_versions()
    project["tool"]["poetry"]["name"] = lock_package_name(
        project["tool"]["poetry"]["name"]
    )
    project["tool"]["poetry"]["description"] = (
        project["tool"]["poetry"]["description"] + " lock package"
    ).strip()
    project["tool"]["poetry"]["dependencies"] = {
        name: f"=={version}" for (name, version) in dependencies.items()
    }
    project["tool"]["poetry"]["dev-dependencies"] = {}

    create_or_update(project)


def create_or_update(project):
    lock_project_path = project["tool"]["poetry"]["name"]
    module_directory = os.path.join(
        lock_project_path,
        project["tool"]["poetry"]["name"].replace("-", "_"),
    )
    os.makedirs(module_directory, exist_ok=True)
    module_init = os.path.join(module_directory, "__init__.py")
    if not os.path.exists(module_init):
        with open(module_init, "w") as module_init_file:
            module_init_file.write(
                '__version__ = "{}"\n'.format(project["tool"]["poetry"]["version"])
            )
    with open(
        os.path.join(lock_project_path, "pyproject.toml"), "w"
    ) as requirements_toml:
        toml.dump(project, requirements_toml)
    return


if __name__ == "__main__":
    main()
