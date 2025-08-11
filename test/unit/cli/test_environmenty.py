import pytest
from click.testing import CliRunner

from exasol_integration_test_docker_environment.cli.commands.environment import (
    environment as environment_command,
)
from exasol_integration_test_docker_environment.cli.options.test_environment_options import (
    DEFAULT_DISK_SIZE,
    DEFAULT_MEM_SIZE,
    LATEST_DB_VERSION,
)


def test_environment():
    runner = CliRunner()
    result = runner.invoke(environment_command, ["--show-default-db-version"])
    assert LATEST_DB_VERSION in result.stdout
    result = runner.invoke(environment_command, ["--show-default-mem-size"])
    assert DEFAULT_MEM_SIZE in result.stdout
    result = runner.invoke(environment_command, ["--show-default-disk-size"])
    assert DEFAULT_DISK_SIZE in result.stdout
