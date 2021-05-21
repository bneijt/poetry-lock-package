Poetry lock package generator
=========================


Simple script that will take a `pyproject.toml` and a `poetry.lock` and generate a new poetry project where all the lock versions are pinned dependencies.

In theory this will allow you to transport your lock file to any system that is able to install python packages and dependencies.

After installation, the command `poetry-lock-package` should be run next to your `pyproject.toml` and `poetry.lock` files and will generate a subdirectory with a `pyproject.toml` requiring all the dependencies of the lock file.

Simply enter the subdirectory, build and publish the package and you have a '-lock' package that depends on all the exact versions from your lock file.


Example workflow
---------------
The example workflow below will add `poetry-lock-package` as a dev dependency, allowing `poetry run` to find the command.

First create a new poetry project

    poetry new example-package
    cd example-package

Add some dependencies, and see what we have build so far

    poetry add loguru click
    poetry install
    poetry build
    ls dist

Add `poetry-lock-package` to allow for `poetry run` to find the entry point script:

    poetry add --dev poetry-lock-package

Finally build the lock package and see what we have gotten

    poetry run poetry-lock-package --build
    ls -al dist

You will now have two wheel files in your dist folder: one with the project code, one name `example-package-lock` which depends on the exact version of all the packages specified in your `poetry.lock` file.

Using `--no-root`
-----------------
Default behavior is to have the lock package depend on the original package the lock was created for. If you have a private repository, this will allow you to publish both packages to the private repository and only require you to point at one package to install everything.

If you want to be able to install the dependencies, but not the package itself, you can use the `--no-root` command line argument to stop `poetry-lock-package` from adding your root project to the lock package dependencies.

Using `--ignore`
----------------
If you want to allow pip to have freedom in selecting a package, or you expect to deploy in an environment that already has the right version installed, you can opt to use `--ignore` to remove that dependency from the lock package pinned dependencies.

Because `poetry-lock-package` is aware of the dependency graph, it will not only skip locking the dependency but also transitive dependencies.

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

