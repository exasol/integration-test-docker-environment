from unittest.mock import MagicMock, Mock
from exasol_integration_test_docker_environment \
    .lib.base.db_os_executor import (
        DockerClientFactory,
        DbOsExecutor,
        DockerExecutor,
        SshExecutor,
        DockerExecFactory,
        SshExecFactory,
)
from exasol_integration_test_docker_environment.lib.test_environment.ports import Ports
from exasol_integration_test_docker_environment.lib.data.ssh_info import SshInfo
from exasol_integration_test_docker_environment.lib.data.database_info import DatabaseInfo


def test_docker_client_factory():
    factory = DockerClientFactory()
    client = Mock()
    factory.client = MagicMock(return_value=client)
    testee = DockerExecFactory("container_name", factory)

    executor = testee.executor()
    factory.client.assert_called()
    assert executor._client == client


def test_executor_closes_client():
    container = Mock()
    containers_mock = Mock()
    containers_mock.get = MagicMock(return_value=container)
    client = Mock(containers=containers_mock)
    with DockerExecutor(client, "container_name") as executor:
        executor.exec("sample command")
        container.exec_run.assert_called_with("sample command")
        client.close.assert_not_called()
    client.close.assert_called()


def test_docker_exec_factory():
    factory = DockerExecFactory("container_name")
    executor = factory.executor()
    assert isinstance(executor, DbOsExecutor)
    assert type(executor) is DockerExecutor


def test_ssh_exec_factory():
    factory = SshExecFactory("connect_string", "ssh_key_file")
    executor = factory.executor()
    assert isinstance(executor, DbOsExecutor)
    assert type(executor) is SshExecutor


def test_ssh_exec_factory_from_database_info():
    ports = Ports(1,2,3)
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