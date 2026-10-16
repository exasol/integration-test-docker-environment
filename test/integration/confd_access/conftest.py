"""Fixtures for raw ConfD access integration scenarios."""

import contextlib
import socket
import time
from collections.abc import Generator
from test.integration.confd_access.json_rpc import create_json_rpc_access

import fabric
import pytest

from exasol_integration_test_docker_environment.lib.base.ssh_access import (
    SshKey,
)
from exasol_integration_test_docker_environment.lib.models.data.database_info import (
    DatabaseInfo,
)
from exasol_integration_test_docker_environment.lib.test_environment.ports import (
    find_free_ports,
)
from exasol_integration_test_docker_environment.testing.api_test_environment_context_provider import (
    build_api_context_provider,
)


@pytest.fixture(scope="module")
def confd_container_ip_json_rpc_access(api_isolation_module):
    """One direct container-IP environment shared by Basic and token checks."""
    env_context = build_api_context_provider(api_isolation_module)
    with env_context(additional_parameters={"create_confd_user": True}) as environment:
        database_info = environment.environment_info.database_info
        yield create_json_rpc_access(
            environment, f"https://{database_info.host}:443/rest"
        )


@pytest.fixture(scope="module")
def confd_published_json_rpc_access(api_isolation_module):
    """One published environment shared by Basic and token checks."""
    confd_port = find_free_ports(1)[0]
    env_context = build_api_context_provider(api_isolation_module)
    with env_context(
        additional_parameters={
            "confd_port_forward": confd_port,
            "create_confd_user": True,
        }
    ) as environment:
        yield create_json_rpc_access(
            environment, f"https://127.0.0.1:{confd_port}/rest"
        )


@pytest.fixture(scope="module")
def confd_ssh_tunnel_json_rpc_access(api_isolation_module):
    """One SSH environment and tunnel shared by Basic and token checks."""
    local_port = find_free_ports(1)[0]
    env_context = build_api_context_provider(api_isolation_module)
    with env_context(
        additional_parameters={"db_os_access": "SSH", "create_confd_user": True}
    ) as environment:
        database_info = environment.environment_info.database_info
        with _ssh_tunnel(database_info, local_port) as endpoint:
            yield create_json_rpc_access(environment, endpoint)


@contextlib.contextmanager
def _ssh_tunnel(
    database_info: DatabaseInfo, local_port: int
) -> Generator[str, None, None]:
    """Forward a local port to the internal ConfD endpoint through ITDE SSH."""
    forwarded_ports = database_info.forwarded_ports
    assert forwarded_ports is not None
    ssh_port = forwarded_ports.ssh
    assert ssh_port is not None
    ssh_host = database_info.port_bind_address or "127.0.0.1"
    key = SshKey.from_cache()
    connection = fabric.Connection(
        f"root@{ssh_host}:{ssh_port}",
        connect_kwargs={"pkey": key.private},
    )
    with connection.forward_local(
        local_port,
        remote_host=database_info.host,
        remote_port=443,
        local_host="127.0.0.1",
    ):
        _wait_for_local_tunnel(local_port)
        yield f"https://127.0.0.1:{local_port}/rest"


def _wait_for_local_tunnel(local_port: int) -> None:
    deadline = time.monotonic() + 5
    while True:
        try:
            with socket.create_connection(("127.0.0.1", local_port), timeout=1):
                return
        except OSError:
            if time.monotonic() >= deadline:
                pytest.fail("SSH tunnel did not start listening on the local port")
            time.sleep(0.1)
