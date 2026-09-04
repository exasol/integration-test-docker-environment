"""ITDE coverage for the opt-in, local ConfD JSON-RPC boundary."""

from exasol_integration_test_docker_environment.lib.api import (
    extract_confd_bearer_token,
)
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.test_environment.ports import (
    find_free_ports,
)


def test_confd_port_is_forwarded_only_to_loopback_and_token_is_extractable(
    api_context,
):
    """The token stays out of environment metadata and Docker binds localhost."""
    confd_port = find_free_ports(1)[0]
    with api_context(
        additional_parameters={"confd_port_forward": confd_port},
    ) as environment:
        environment_info = environment.environment_info
        database_info = environment_info.database_info
        container_info = database_info.container_info
        assert container_info is not None
        assert database_info.forwarded_ports is not None
        assert database_info.forwarded_ports.confd == confd_port
        assert not hasattr(environment_info, "confd_bearer_token")

        with ContextDockerClient() as docker_client:
            container = docker_client.containers.get(container_info.container_name)
            container.reload()
        bindings = container.attrs["NetworkSettings"]["Ports"]
        assert bindings["443/tcp"] == [
            {"HostIp": "127.0.0.1", "HostPort": str(confd_port)}
        ]

        # Deliberately do not include this secret in assertions or test output.
        assert extract_confd_bearer_token(environment_info)
