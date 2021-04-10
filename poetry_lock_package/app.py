import toml
import os


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


def main():
    project = read_project()
    dependencies = read_lock_versions()
    separator = "_" if "_" in project["tool"]["poetry"]["name"] else "-"
    project["tool"]["poetry"]["name"] = (
        project["tool"]["poetry"]["name"] + separator + "lock"
    )
    project["tool"]["poetry"]["description"] += " lock package"
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
                "from importlib_metadata import version\n__version__ = version(__name__)"
            )
    with open(
        os.path.join(lock_project_path, "pyproject.toml"), "w"
    ) as requirements_toml:
        toml.dump(project, requirements_toml)
    return


if __name__ == "__main__":
    main()
