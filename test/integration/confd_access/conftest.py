"""Fixtures for raw ConfD access integration scenarios."""

import contextlib
import socket
import time
from collections.abc import Generator
from dataclasses import dataclass

import fabric
import pytest
from docker.models.containers import Container

from exasol_integration_test_docker_environment.lib.base.ssh_access import (
    SshKey,
)
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.models.data.database_info import (
    DatabaseInfo,
)
from exasol_integration_test_docker_environment.lib.test_environment.ports import (
    find_free_ports,
)


@dataclass(frozen=True)
class ConfdContainerAccess:
    """Temporary ConfD credentials and the database container endpoint."""

    host: str
    username: str
    password: str


@dataclass(frozen=True)
class ConfdJsonRpcAccess:
    """A ready-to-use HTTPS JSON-RPC endpoint and disposable credentials."""

    endpoint: str
    username: str
    password: str


@dataclass(frozen=True)
class ConfdJsonRpcTokenAccess:
    """A JSON-RPC endpoint and its EXAConf authentication token."""

    endpoint: str
    token: str


@pytest.fixture
def confd_container_ip_json_rpc_basic_access(api_context):
    """Direct container-IP JSON-RPC endpoint with the ready Basic account."""

    @contextlib.contextmanager
    def create_context() -> Generator[ConfdContainerAccess, None, None]:
        with api_context(
            additional_parameters={"create_confd_user": True}
        ) as environment:
            database_info = environment.environment_info.database_info
            confd_info = database_info.confd_info
            assert confd_info is not None
            credentials = confd_info.read_credentials()
            yield ConfdContainerAccess(
                database_info.host, credentials.username, credentials.password
            )

    return create_context


@pytest.fixture
def confd_published_json_rpc_basic_access(api_context):
    """ITDE-published localhost JSON-RPC endpoint with Basic credentials."""

    @contextlib.contextmanager
    def create_context() -> Generator[ConfdJsonRpcAccess, None, None]:
        confd_port = find_free_ports(1)[0]
        with api_context(
            additional_parameters={
                "confd_port_forward": confd_port,
                "create_confd_user": True,
            }
        ) as environment:
            confd_info = environment.environment_info.database_info.confd_info
            assert confd_info is not None
            credentials = confd_info.read_credentials()
            yield ConfdJsonRpcAccess(
                endpoint=f"https://127.0.0.1:{confd_port}/rest",
                username=credentials.username,
                password=credentials.password,
            )

    return create_context


@pytest.fixture
def confd_container_ip_json_rpc_token_access(api_context):
    """Direct container-IP JSON-RPC endpoint with the EXAConf authentication token."""

    @contextlib.contextmanager
    def create_context() -> Generator[ConfdJsonRpcTokenAccess, None, None]:
        with api_context(
            additional_parameters={"create_confd_user": True}
        ) as environment:
            database_info = environment.environment_info.database_info
            container_info = database_info.container_info
            assert container_info is not None
            with ContextDockerClient() as docker_client:
                container = docker_client.containers.get(container_info.container_name)
                token = _read_authentication_token(container)
            yield ConfdJsonRpcTokenAccess(
                endpoint=f"https://{database_info.host}:443/rest",
                token=token,
            )

    return create_context


@pytest.fixture
def confd_published_json_rpc_token_access(api_context):
    """ITDE-published localhost JSON-RPC endpoint with the EXAConf authentication token."""

    @contextlib.contextmanager
    def create_context() -> Generator[ConfdJsonRpcTokenAccess, None, None]:
        confd_port = find_free_ports(1)[0]
        with api_context(
            additional_parameters={
                "confd_port_forward": confd_port,
                "create_confd_user": True,
            }
        ) as environment:
            database_info = environment.environment_info.database_info
            container_info = database_info.container_info
            assert container_info is not None
            with ContextDockerClient() as docker_client:
                container = docker_client.containers.get(container_info.container_name)
                token = _read_authentication_token(container)
            yield ConfdJsonRpcTokenAccess(
                endpoint=f"https://127.0.0.1:{confd_port}/rest",
                token=token,
            )

    return create_context


@pytest.fixture
def confd_ssh_tunnel_json_rpc_basic_access(api_context):
    """SSH-tunneled JSON-RPC endpoint with disposable Basic credentials."""

    @contextlib.contextmanager
    def create_context() -> Generator[ConfdJsonRpcAccess, None, None]:
        local_port = find_free_ports(1)[0]
        with api_context(
            additional_parameters={
                "db_os_access": "SSH",
                "create_confd_user": True,
            }
        ) as environment:
            database_info = environment.environment_info.database_info
            confd_info = database_info.confd_info
            assert confd_info is not None
            credentials = confd_info.read_credentials()
            with _ssh_tunnel(database_info, local_port) as endpoint:
                yield ConfdJsonRpcAccess(
                    endpoint=endpoint,
                    username=credentials.username,
                    password=credentials.password,
                )

    return create_context


@pytest.fixture
def confd_ssh_tunnel_json_rpc_token_access(api_context):
    """SSH-tunneled JSON-RPC endpoint with the EXAConf authentication token."""

    @contextlib.contextmanager
    def create_context() -> Generator[ConfdJsonRpcTokenAccess, None, None]:
        local_port = find_free_ports(1)[0]
        with api_context(
            additional_parameters={
                "db_os_access": "SSH",
                "create_confd_user": True,
            }
        ) as environment:
            database_info = environment.environment_info.database_info
            container_info = database_info.container_info
            assert container_info is not None
            with ContextDockerClient() as docker_client:
                container = docker_client.containers.get(container_info.container_name)
                token = _read_authentication_token(container)
            with _ssh_tunnel(database_info, local_port) as endpoint:
                yield ConfdJsonRpcTokenAccess(
                    endpoint=endpoint,
                    token=token,
                )

    return create_context


def _read_authentication_token(container: Container) -> str:
    result = container.exec_run(
        "awk -F' = ' '/AuthenticationToken/ {print $2; exit}' /exa/etc/EXAConf"
    )
    if result.exit_code != 0 or not result.output.strip():
        pytest.fail("ConfD bearer-token test setup failed")
    return result.output.decode().strip()


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
