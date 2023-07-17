from abc import abstractmethod
import fabric
import docker
from docker import DockerClient
from typing import Optional, Protocol, runtime_checkable
from docker.models.containers import Container, ExecResult
from exasol_integration_test_docker_environment \
    .lib.base.ssh_access import SshKey
from exasol_integration_test_docker_environment \
    .lib.data.database_info import DatabaseInfo
from exasol_integration_test_docker_environment.lib.docker \
    import ContextDockerClient


class DockerClientFactory(Protocol):
    """
    Create a Docker client.
    """
    @abstractmethod
    def client(self) -> DockerClient:
        ...

class DockerClientFactory:
    def __init__(self, timeout: int = 100000):
        self._timeout = timeout

    def client(self) -> DockerClient:
        return ContextDockerClient(timeout=self._timeout)


@runtime_checkable
class DbOsExecutor(Protocol):
    """
    This class provides an abstraction to execute commands inside a Docker
    Container.  See concrete implementations in sub-classes
    ``DockerExecutor`` and ``SshExecutor``.
    """
    @abstractmethod
    def exec(self, cmd: str) -> ExecResult:
        ...


class DockerExecutor(DbOsExecutor):
    def __init__(self, docker_client: DockerClient, container_name: str):
        self._client = docker_client
        self._container_name = container_name
        self._container = None

    def __enter__(self):
        self._container = self._client.containers.get(self._container_name)
        return self

    def __exit__(self, type_, value, traceback):
        self._container = None
        self._client.close()
        self._client = None

    def exec(self, cmd: str):
        return self._container.exec_run(cmd)


class SshExecutor(DbOsExecutor):
    def __init__(self, connect_string: str, key_file: str):
        self._connect_string = connect_string
        self._key_file = key_file
        self._connection = None

    def __enter__(self):
        key = SshKey.read_from(self._key_file)
        self._connection = fabric.Connection(
            self._connect_string,
            connect_kwargs={ "pkey": key.private },
        )
        return self

    def __exit__(self, type_, value, traceback):
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def exec(self, cmd: str) -> ExecResult:
        # monkeypatch.setattr('sys.stdin', io.StringIO(''))
        result = self._connection.run(cmd)
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
    def __init__(
            self,
            container_name: str,
            client_factory: Optional[DockerClientFactory] = None,
    ):
        self._container_name = container_name
        if client_factory is None:
            client_factory = DockerClientFactory()
        self._client_factory = client_factory

    def executor(self) -> DbOsExecutor:
        client = self._client_factory.client()
        return DockerExecutor(client, self._container_name)


class SshExecFactory(DbOsExecFactory):
    @classmethod
    def from_database_info(cls, info: DatabaseInfo):
        return SshExecFactory(
            f"{info.ssh_info.user}@{info.host}:{info.ports.ssh}",
            info.ssh_info.key_file,
        )

    def __init__(self, connect_string: str, ssh_key_file: str):
        self._connect_string = connect_string
        self._key_file = ssh_key_file

    def executor(self) -> DbOsExecutor:
        return SshExecutor(self._connect_string, self._key_file)