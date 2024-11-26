#! /usr/bin/env python3
#
from exasol_integration_test_docker_environment.cli.cli import cli


def main():
    # required so the cli will print the available subcommands
    from exasol_integration_test_docker_environment.cli.commands import (
        health,
        spawn_test_environment,
    )

    cli()


if __name__ == "__main__":
    main()
