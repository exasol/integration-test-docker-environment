from test.integration.helpers import mock_cast
from unittest.mock import (
    MagicMock,
    call,
    create_autospec,
)

import pytest
from docker import DockerClient
from docker.models.containers import Container as DockerContainer
from paramiko.ssh_exception import SSHException

from exasol_integration_test_docker_environment.lib.base.db_os_executor import (
    DbOsExecutor,
    DockerClientFactory,
    DockerExecFactory,
    DockerExecutor,
    SshExecFactory,
    SshExecutor,
)
from exasol_integration_test_docker_environment.lib.models.data.database_info import (
    DatabaseInfo,
)
from exasol_integration_test_docker_environment.lib.models.data.ssh_info import SshInfo
from exasol_integration_test_docker_environment.lib.test_environment.ports import Ports


def test_executor_closes_client():
    container = create_autospec(DockerContainer)
    client: MagicMock | DockerClient = create_autospec(DockerClient)
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


def test_ssh_exec_factory_prefers_forwarded_docker_port():
    dbinfo = DatabaseInfo(
        "172.18.0.2",
        Ports(8563, 2580, 22),
        reused=False,
        ssh_info=SshInfo("root", "fixture-key"),
        forwarded_ports=Ports(8563, 2580, 30123),
    )

    executor = SshExecFactory.from_database_info(dbinfo).executor()

    assert executor._connect_string == "root@127.0.0.1:30123"
    assert executor._key_file == "fixture-key"


def test_ssh_exec_factory_uses_database_endpoint_without_forwarded_ssh_port():
    dbinfo = DatabaseInfo(
        "172.18.0.2",
        Ports(8563, 2580, 22),
        reused=False,
        ssh_info=SshInfo("root", "fixture-key"),
        forwarded_ports=Ports(8563, 2580),
    )

    executor = SshExecFactory.from_database_info(dbinfo).executor()

    assert executor._connect_string == "root@172.18.0.2:22"


def test_ssh_prepare_retries_until_sshd_is_ready(monkeypatch):
    executor = SshExecutor("root@127.0.0.1:30123", "fixture-key")
    connection = MagicMock()
    connection.run.side_effect = [SSHException("SSH banner not ready"), None]
    executor._connection = connection
    sleep = MagicMock()
    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.base.db_os_executor.time.sleep",
        sleep,
    )

    executor.prepare()

    assert connection.run.call_count == 2
    connection.close.assert_called_once()
    sleep.assert_called_once_with(1)


def test_ssh_prepare_requires_an_open_connection():
    executor = SshExecutor("root@127.0.0.1:30123", "fixture-key")

    with pytest.raises(
        RuntimeError, match=r"^SSH executor must be entered before preparation$"
    ):
        executor.prepare()


def test_ssh_prepare_raises_after_retry_limit(monkeypatch):
    executor = SshExecutor("root@127.0.0.1:30123", "fixture-key")
    connection = MagicMock()
    connection.run.side_effect = SSHException("SSH banner not ready")
    executor._connection = connection
    sleep = MagicMock()
    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.base.db_os_executor.time.sleep",
        sleep,
    )

    with pytest.raises(SSHException, match="SSH banner not ready"):
        executor.prepare()

    assert connection.run.call_count == 20
    assert connection.close.call_count == 20
    assert sleep.call_count == 19
