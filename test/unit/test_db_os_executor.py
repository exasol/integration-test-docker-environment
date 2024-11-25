from test.integration.helpers import mock_cast
from unittest.mock import (
    MagicMock,
    call,
    create_autospec,
)

from docker import DockerClient
from docker.models.containers import Container as DockerContainer

from exasol_integration_test_docker_environment.lib.base.db_os_executor import (
    DbOsExecutor,
    DockerClientFactory,
    DockerExecFactory,
    DockerExecutor,
    SshExecFactory,
    SshExecutor,
)
from exasol_integration_test_docker_environment.lib.data.database_info import (
    DatabaseInfo,
)
from exasol_integration_test_docker_environment.lib.data.ssh_info import SshInfo
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.test_environment.ports import Ports


def test_executor_closes_client():
    container = create_autospec(DockerContainer)
    client: Union[MagicMock, DockerClient] = create_autospec(DockerClient)
    client.containers.get = MagicMock(return_value=container)
    with DockerExecutor(client, "container_name") as executor:
        executor.exec("sample command")
        container.exec_run.assert_called_with("sample command")
        client.close.assert_not_called()
    client.close.assert_called()


def test_ssh_exec_factory():
    factory = SshExecFactory("connect_string", "ssh_key_file")
    executor = factory.executor()
    assert isinstance(executor, DbOsExecutor) and type(executor) is SshExecutor


def test_docker_exec_factory():
    client_factory = create_autospec(DockerClientFactory)
    factory = DockerExecFactory("container_name", client_factory)
    executor = factory.executor()
    assert isinstance(executor, DbOsExecutor) and type(executor) is DockerExecutor


def test_docker_client_factory_usage():
    client = create_autospec(DockerClient)
    factory = create_autospec(DockerClientFactory)
    factory.client = MagicMock(return_value=client)
    testee = DockerExecFactory("container_name", factory)
    executor = testee.executor()
    assert executor._client == client and mock_cast(factory.client).mock_calls == [
        call()
    ]


def test_ssh_exec_factory_from_database_info():
    ports = Ports(1, 2, 3)
    ssh_info = SshInfo("my_user", "my_key_file")
    dbinfo = DatabaseInfo(
        "my_host",
        ports,
        reused=False,
        container_info=None,
        ssh_info=ssh_info,
        forwarded_ports=None,
    )
    factory = SshExecFactory.from_database_info(dbinfo)
    executor = factory.executor()
    assert executor._connect_string == "my_user@my_host:3"
    assert executor._key_file == "my_key_file"
