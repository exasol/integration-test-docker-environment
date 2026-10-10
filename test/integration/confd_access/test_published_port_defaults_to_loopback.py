"""Default ConfD published-port binding integration scenario."""

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.test_environment.ports import (
    find_free_ports,
)


def test_published_port_defaults_to_loopback(api_context):
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
