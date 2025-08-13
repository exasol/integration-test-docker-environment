import sys

import click

from exasol_integration_test_docker_environment.cli.cli import cli
from exasol_integration_test_docker_environment.cli.options.test_environment_options import (
    DEFAULT_DISK_SIZE,
    DEFAULT_MEM_SIZE,
    LATEST_DB_VERSION,
)


@cli.command()
@click.option(
    "--show-default-db-version",
    is_flag=True,
    help="Displays the defualt Docker DB Image version",
)
@click.option(
    "--show-default-mem-size",
    is_flag=True,
    help="Displays the defualt DB mem size",
)
@click.option(
    "--show-default-disk-size",
    is_flag=True,
    help="Displays the defualt DB disk size",
)
def environment(
    show_default_db_version: bool,
    show_default_mem_size: bool,
    show_default_disk_size: bool,
):
    """
    Displays the default configurations of the DB.
    """
    if show_default_db_version:
        print(f"Default Docker DB Image Version: {LATEST_DB_VERSION}")
    elif show_default_mem_size:
        print(f"Default DB mem size: {DEFAULT_MEM_SIZE}")
    elif show_default_disk_size:
        print(f"Default DB disk size: {DEFAULT_DISK_SIZE}")
