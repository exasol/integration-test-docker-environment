#! /usr/bin/env python3
#
from exasol_integration_test_docker_environment.cli.cli import cli


def main():
    # The imports from `commands` are required so that `cli()` will print the available
    # subcommands. Unfortunately, as these are unused imports within this file, an
    # auto-formatting tool would want to remove them.
    from exasol_integration_test_docker_environment.cli.commands import (  # noqa: F401
        environment,
        health,
        spawn_test_environment,
    )

    cli()


if __name__ == "__main__":
    main()
