#! /usr/bin/env python3
#
from src.cli.cli import cli
# noinspection PyUnresolvedReferences
from src.cli.commands import spawn_test_environment, push_test_container, build_test_container

if __name__ == '__main__':
    cli()
