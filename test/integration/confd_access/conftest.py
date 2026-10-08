"""Fixtures for raw ConfD access integration scenarios."""

import contextlib
import secrets
from collections.abc import Generator
from dataclasses import dataclass

import fabric
import pytest
from docker.models.containers import Container

from exasol_integration_test_docker_environment.lib.base.db_os_executor import (
    DbOsExecutor,
    DockerClientFactory,
    DockerExecFactory,
    SshExecFactory,
)
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
    """A container-IP JSON-RPC endpoint and its disposable bearer token."""

    endpoint: str
    token: str


def _run_confd(container: Container, command: str, password: str | None = None) -> None:
    environment = {} if password is None else {"CONFD_PASSWORD": password}
    result = container.exec_run(command, environment=environment)
    if result.exit_code != 0:
        pytest.fail("ConfD test-user setup or cleanup failed")


def _create_user(
    container: Container, username: str, user_id: int, password: str
) -> None:
    command = (
        "confd_client -c user_create -A "
        f'\'{{"username":"{username}","userid":{user_id},'
        '"group":"exaadm","login_enabled":true,"password":"\''
        '"$CONFD_PASSWORD"'
        '\'","encode_passwd":true}\''
    )
    _run_confd(container, command, password)


def _delete_user(container: Container, username: str) -> None:
    _run_confd(
        container,
        f'confd_client -c user_delete -A \'{{"username":"{username}"}}\'',
    )


@pytest.fixture
def confd_container_ip_json_rpc_basic_access(api_context):
    """Direct container-IP JSON-RPC endpoint with a disposable Basic user."""

    @contextlib.contextmanager
    def create_context() -> Generator[ConfdContainerAccess, None, None]:
        username = f"itde_spike_{secrets.token_hex(8)}"
        password = secrets.token_urlsafe(32)
        user_id = 30000 + secrets.randbelow(10000)
        with api_context() as environment:
            database_info = environment.environment_info.database_info
            container_info = database_info.container_info
            assert container_info is not None
            with ContextDockerClient() as docker_client:
                container = docker_client.containers.get(container_info.container_name)
                _create_user(container, username, user_id, password)
                try:
                    yield ConfdContainerAccess(database_info.host, username, password)
                finally:
                    _delete_user(container, username)

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
    """Direct container-IP JSON-RPC endpoint with the EXAConf bearer token."""

    @contextlib.contextmanager
    def create_context() -> Generator[ConfdJsonRpcTokenAccess, None, None]:
        with api_context() as environment:
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
    """ITDE-published localhost JSON-RPC endpoint with the EXAConf token."""

    @contextlib.contextmanager
    def create_context() -> Generator[ConfdJsonRpcTokenAccess, None, None]:
        confd_port = find_free_ports(1)[0]
        with api_context(
            additional_parameters={"confd_port_forward": confd_port}
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
    """SSH-tunneled JSON-RPC endpoint with the EXAConf bearer token."""

    @contextlib.contextmanager
    def create_context() -> Generator[ConfdJsonRpcTokenAccess, None, None]:
        local_port = find_free_ports(1)[0]
        with api_context(additional_parameters={"db_os_access": "SSH"}) as environment:
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


@pytest.fixture
def confd_client_ssh_executor(api_context):
    """Expose explicit ``confd_client`` command execution through ITDE SSH."""

    @contextlib.contextmanager
    def create_context() -> Generator[DbOsExecutor, None, None]:
        with api_context(additional_parameters={"db_os_access": "SSH"}) as environment:
            database_info = environment.environment_info.database_info
            with SshExecFactory.for_host(database_info).executor() as executor:
                executor.prepare()
                yield executor

    return create_context


@pytest.fixture
def confd_client_docker_exec_executor(api_context):
    """Expose explicit ``confd_client`` execution through Docker exec."""

    @contextlib.contextmanager
    def create_context() -> Generator[DbOsExecutor, None, None]:
        with api_context() as environment:
            container_info = environment.environment_info.database_info.container_info
            assert container_info is not None
            factory = DockerExecFactory(
                container_info.container_name,
                DockerClientFactory(),
            )
            with factory.executor() as executor:
                executor.prepare()
                yield executor

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
    published_ssh_port = database_info.published_port("ssh")
    assert published_ssh_port is not None
    ssh_host, ssh_port = published_ssh_port.local_endpoint()
    key = SshKey.from_cache()
    connection = fabric.Connection(
        f"root@{ssh_host}:{ssh_port}",
        connect_kwargs={"pkey": key.private},
    )
    with connection.forward_local(
        local_port,
        remote_host=database_info.host,
        remote_port=443,
    ):
        yield f"https://127.0.0.1:{local_port}/rest"
