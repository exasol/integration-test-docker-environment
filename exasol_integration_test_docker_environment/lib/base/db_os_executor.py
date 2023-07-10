from abc import abstractmethod
import fabric
import docker
from typing import Protocol, runtime_checkable
from docker.models.containers import Container, ExecResult
from exasol_integration_test_docker_environment \
    .lib.base.ssh_access import SshKey
from exasol_integration_test_docker_environment \
    .lib.data.database_info import DatabaseInfo


@runtime_checkable
class DbOsExecutor(Protocol):
    """
    This class provides an abstraction to execute commands inside a Docker
    Container.  See concrete implementations in sub-classes
    ``PlainDockerExec`` and ``SshDockerExec``.
    """
    @abstractmethod
    def exec(self, cmd: str) -> ExecResult:
        ...


class DockerExecutor(DbOsExecutor):
    def __init__(self, container_name: str, timeout: int = 100000):
        self.container_name = container_name
        self.timeout = timeout
        self.container = None

    def _get_docker_client(self):
        return ContextDockerClient(timeout=self.timeout)

    def _find_container():
        if not self.container:
            with self._get_docker_client() as client:
                self.container = client.containers.get(self.container_name)
        return self.container

    def exec(self, cmd: str):
        return self._find_container().exec_run(cmd)


class SshExecutor(DbOsExecutor):
    def __init__(self, connect_string: str, key_file: str):
        self.connect_string = connect_string
        self.key_file = key_file
        self.connection = None

    def _connection(self):
        if self.connection is None:
            key = SshKey.read_from(self.key_file)
            self.connection = fabric.Connection(
                self.connect_string,
                connect_kwargs={ "pkey": key.private },
            )
        return self.connection

    def exec(self, cmd: str) -> ExecResult:
        # monkeypatch.setattr('sys.stdin', io.StringIO(''))
        result = self._connection().run(cmd)
        return ExecResult(result.exited, result.stdout)


@runtime_checkable
class DbOsExecFactory(Protocol):
    """
    This class defines abstract method ``executor()`` to be implemented by
    inheriting factories.
    """

    @abstractmethod
    def executor(self) -> DbOsExecutor:
        """Create an executor for executing commands inside a Docker
        Container."""
        ...


class DockerExecFactory(DbOsExecFactory):
    def __init__(self, container_name: str, timeout: int = 100000):
        self.container_name = container_name
        self.timeout = timeout

    def executor(self) -> DbOsExecutor:
        return DockerExecutor(self.container_name, self.timeout)


class SshExecFactory(DockerExecFactory):
    @classmethod
    def from_database_info(cls, info: DatabaseInfo):
        return SshExecFactory(
            f"{info.ssh_info.user}@{info.host}:{info.ports.ssh}",
            info.ssh_info.key_file,
        )

    def __init__(self, connect_string: str, ssh_key_file: str):
        self.connect_string = connect_string
        self.key_file = ssh_key_file

    def executor(self) -> DbOsExecutor:
        return SshExecutor(self.connect_string, self.key_file)
