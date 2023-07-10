from exasol_integration_test_docker_environment \
    .lib.base.db_os_executor import (
        DbOsExecutor,
        DockerExecutor,
        SshExecutor,
        DockerExecFactory,
        SshExecFactory,
)
from exasol_integration_test_docker_environment.lib.test_environment.ports import Ports
from exasol_integration_test_docker_environment.lib.data.ssh_info import SshInfo
from exasol_integration_test_docker_environment.lib.data.database_info import DatabaseInfo


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
    assert executor.connect_string == "my_user@my_host:3"
    assert executor.key_file == "my_key_file"
