from cleo.events.console_events import COMMAND
from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.event_dispatcher import EventDispatcher
from poetry.console.application import Application
from poetry.console.commands.build import BuildCommand
from poetry.plugins.application_plugin import ApplicationPlugin
from functools import wraps
from poetry.poetry import Poetry
from poetry.core.packages.dependency_group import MAIN_GROUP
from poetry_plugin_export.walker import get_project_dependency_packages
from poetry.core.packages.dependency import Dependency


def locked_dependencies(poetry: Poetry) -> list[Dependency]:
    locked_deps = []
    root = poetry.package.with_dependency_groups({MAIN_GROUP}, only=True)
    print("ROOT", root)
    print("root deps", root.all_requires)
    for dependency_package in get_project_dependency_packages(
        poetry.locker,
        project_requires=root.all_requires,
        root_package_name=root.name,
        project_python_marker=root.python_marker,
        extras=[],
    ):
        print("FOUND dependency_package", dependency_package)
        dependency_package = dependency_package.without_features()

        dependency = dependency_package.dependency

        if (
            dependency.is_file()
            or dependency.is_directory()
            or dependency.is_vcs()
            or dependency.is_url()
        ):
            continue
        locked_deps.append(dependency)
    return locked_deps


class LockPackagePlugin(ApplicationPlugin):
    def activate(self, application: Application):
        application.event_dispatcher.add_listener(COMMAND, self.command_handler)

    def command_handler(
        self, event: ConsoleCommandEvent, event_name: str, dispatcher: EventDispatcher
    ) -> None:
        command = event.command
        if not isinstance(command, BuildCommand):
            return
        from poetry.core.masonry.builders.wheel import WheelBuilder

        io = event.io
        extra_name = "locked"

        def wrap_metadata(f):
            @wraps(f)
            def wrapper(self, *args, **kwds):
                io.write_line(f"Adding '{extra_name}' extra")
                self._meta.provides_extra.append(extra_name)
                deps = locked_dependencies(self._poetry)
                for dep in deps:
                    pirnt("ADDING DEP", dep)
                    self._meta.requires_dist.append(
                        dep.to_pep_508() + f"; extra == '{extra_name}'"
                    )
                return f(self, *args, **kwds)

            return wrapper

        WheelBuilder.get_metadata_content = wrap_metadata(
            WheelBuilder.get_metadata_content
        )

        if io.is_debug():
            io.write_line("<debug>Loading environment variables.</debug>")
