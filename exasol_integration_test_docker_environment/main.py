#! /usr/bin/env python3
#
from exasol_integration_test_docker_environment.cli.cli import cli
# noinspection PyUnresolvedReferences
from exasol_integration_test_docker_environment.cli.commands import (
    doctor,
    spawn_test_environment,
    push_test_container,
    build_test_container
)

if __name__ == '__main__':
    cli()
