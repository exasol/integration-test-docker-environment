from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from exasol_integration_test_docker_environment.lib.api.confd import (
    extract_confd_bearer_token,
)


def _environment(container_name: str = "itde-db"):
    return SimpleNamespace(
        database_info=SimpleNamespace(
            container_info=SimpleNamespace(container_name=container_name)
        )
    )


def test_extract_confd_bearer_token_reads_the_disposable_container(monkeypatch):
    client = MagicMock()
    client.containers.get.return_value.exec_run.return_value = SimpleNamespace(
        exit_code=0, output=b"test-token\n"
    )
    context = MagicMock()
    context.__enter__.return_value = client
    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.api.confd.ContextDockerClient",
        lambda: context,
    )

    assert extract_confd_bearer_token(_environment()) == "test-token"
    client.containers.get.assert_called_once_with("itde-db")


def test_extract_confd_bearer_token_does_not_include_secret_in_errors(monkeypatch):
    client = MagicMock()
    client.containers.get.return_value.exec_run.return_value = SimpleNamespace(
        exit_code=1, output=b"secret-token"
    )
    context = MagicMock()
    context.__enter__.return_value = client
    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.api.confd.ContextDockerClient",
        lambda: context,
    )

    environment = _environment()
    with pytest.raises(RuntimeError) as error:
        extract_confd_bearer_token(environment)
    assert "secret-token" not in str(error.value)


def test_extract_confd_bearer_token_rejects_non_docker_environments():
    environment = SimpleNamespace(database_info=SimpleNamespace(container_info=None))
    with pytest.raises(ValueError):
        extract_confd_bearer_token(environment)
