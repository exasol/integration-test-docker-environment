from unittest.mock import Mock

from exasol_integration_test_docker_environment.lib.test_environment.ports import Ports
from exasol_integration_test_docker_environment.testing import api_test_environment
from exasol_integration_test_docker_environment.testing.api_test_environment import (
    ApiTestEnvironment,
)


class ApiTestEnvironmentFixture:
    pass


def _environment() -> ApiTestEnvironment:
    return ApiTestEnvironment(ApiTestEnvironmentFixture(), name="api-test-environment")


def test_api_environment_forwards_ssh_port_for_default_docker_exec(monkeypatch):
    ports = Ports(8563, 2580, 2222, 2581)
    spawn = Mock(return_value=(None, Mock()))
    monkeypatch.setattr(api_test_environment.Ports, "random_free", lambda: ports)
    monkeypatch.setattr(api_test_environment, "spawn_test_environment", spawn)
    environment = _environment()

    try:
        environment.spawn_docker_test_environment("default")
    finally:
        environment.close()

    assert spawn.call_args.kwargs["ssh_port_forward"] == ports.ssh


def test_api_environment_with_test_container_forwards_ssh_port(monkeypatch):
    ports = Ports(8563, 2580, 2222, 2581)
    spawn = Mock(return_value=(None, Mock()))
    monkeypatch.setattr(api_test_environment.Ports, "random_free", lambda: ports)
    monkeypatch.setattr(
        api_test_environment, "spawn_test_environment_with_test_container", spawn
    )
    environment = _environment()

    try:
        environment.spawn_docker_test_environment_with_test_container("default", Mock())
    finally:
        environment.close()

    assert spawn.call_args.kwargs["ssh_port_forward"] == ports.ssh
