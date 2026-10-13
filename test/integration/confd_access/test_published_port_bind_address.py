"""Configured ConfD published-port binding integration scenario."""

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.test_environment.ports import (
    find_free_ports,
)


def test_published_port_bind_address(api_context):
    """Docker applies the requested bind address to every forwarded port."""
    confd_port = find_free_ports(1)[0]
    with api_context(
        additional_parameters={
            "confd_port_forward": confd_port,
            "port_bind_address": "127.0.0.1",
        },
    ) as environment:
        database_info = environment.environment_info.database_info
        container_info = database_info.container_info
        assert container_info is not None
        assert database_info.forwarded_ports is not None
        database_port = database_info.forwarded_ports.database
        assert database_info.forwarded_ports.confd == confd_port
        with ContextDockerClient() as docker_client:
            container = docker_client.containers.get(container_info.container_name)
            container.reload()
        bindings = container.attrs["NetworkSettings"]["Ports"]
        assert bindings["8563/tcp"] == [
            {"HostIp": "127.0.0.1", "HostPort": str(database_port)}
        ]
        assert bindings["443/tcp"] == [
            {"HostIp": "127.0.0.1", "HostPort": str(confd_port)}
        ]
