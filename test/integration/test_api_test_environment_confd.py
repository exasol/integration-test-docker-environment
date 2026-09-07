"""ITDE coverage for the opt-in, local ConfD JSON-RPC boundary."""

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.test_environment.ports import (
    find_free_ports,
)


def test_confd_port_defaults_to_loopback(api_context):
    """ConfD remains local when no bind address is explicitly configured."""
    confd_port = find_free_ports(1)[0]
    with api_context(
        additional_parameters={"confd_port_forward": confd_port},
    ) as environment:
        container_info = environment.environment_info.database_info.container_info
        assert container_info is not None
        with ContextDockerClient() as docker_client:
            container = docker_client.containers.get(container_info.container_name)
            container.reload()
        bindings = container.attrs["NetworkSettings"]["Ports"]
        assert bindings["443/tcp"] == [
            {"HostIp": "127.0.0.1", "HostPort": str(confd_port)}
        ]


def test_port_bind_address_applies_to_confd_and_database(api_context):
    """Docker applies the requested bind address to every forwarded port."""
    database_port, confd_port = find_free_ports(2)
    with api_context(
        additional_parameters={
            "database_port_forward": database_port,
            "confd_port_forward": confd_port,
            "port_bind_address": "127.0.0.1",
        },
    ) as environment:
        environment_info = environment.environment_info
        database_info = environment_info.database_info
        container_info = database_info.container_info
        assert container_info is not None
        assert database_info.forwarded_ports is not None
        assert database_info.forwarded_ports.database == database_port
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
