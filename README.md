Poetry lock package generator
=========================


Simple script that will take a `pyproject.toml` and a `poetry.lock` and generate a new poetry project where all the lock versions are pinned dependencies.

In theory this will allow you to transport your lock file to any system that is able to install python packages and dependencies.

After installation, the command `poetry-lock-package` should be run next to your `pyproject.toml` and `poetry.lock` files and will generate a subdirectory with a `pyproject.toml` requiring all the dependencies of the lock file.

Simply enter the subdirectory, build and publish the package and you have a '-lock' package that depends on all the exact versions from your lock file.

License
-------
GPLv3, use at your own risk.

