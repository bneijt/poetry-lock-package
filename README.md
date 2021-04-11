Poetry lock package generator
=========================


Simple script that will take a `pyproject.toml` and a `poetry.lock` and generate a new poetry project where all the lock versions are pinned dependencies.

In theory this will allow you to transport your lock file to any system that is able to install python packages and dependencies.

After installation, the command `poetry-lock-package` should be run next to your `pyproject.toml` and `poetry.lock` files and will generate a subdirectory with a `pyproject.toml` requiring all the dependencies of the lock file.

Simply enter the subdirectory, build and publish the package and you have a '-lock' package that depends on all the exact versions from your lock file.


Example worflow
---------------

Simply put, the workflow is as follows

    pip install poetry poetry-lock-package
    poetry new example-package
    cd example-package
    poetry add loguru
    poetry-lock-package
    cd example-package-lock
    cat pyproject.toml
    poetry install

Contributing code
-----------------

- Open an issue
- Create an associated PR
- Make sure to black format the proposed change

    poetry run pre-commit install

- Add tests where possible

License
-------
GPLv3, use at your own risk.

