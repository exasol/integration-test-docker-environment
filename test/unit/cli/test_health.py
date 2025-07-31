from test.unit.cli.cli_runner import CliRunner
from unittest.mock import (
    MagicMock,
    call,
)

import pytest
from _pytest.monkeypatch import MonkeyPatch

import exasol_integration_test_docker_environment.lib.api as api
from exasol_integration_test_docker_environment.cli.commands.health import (
    health as health_command,
)


@pytest.fixture
def cli():
    return CliRunner(health_command)


@pytest.fixture
def mock_api_health(monkeypatch: MonkeyPatch) -> MagicMock:
    mock_function_to_mock = MagicMock()
    monkeypatch.setattr(api, "health", mock_function_to_mock)
    return mock_function_to_mock


def test_health(cli, mock_api_health):
    cli.run()
    assert cli.succeeded

    # Validate the exact call using mock_calls and IsInstance matcher
    expected_call = call()
    assert mock_api_health.mock_calls == [expected_call]
