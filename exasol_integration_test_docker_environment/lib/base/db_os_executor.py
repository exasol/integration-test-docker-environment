import time
from abc import abstractmethod
from typing import (
    Optional,
    Protocol,
    runtime_checkable,
)

import docker
import fabric
from docker import DockerClient
from docker.models.containers import (
    Container,
    ExecResult,
)
from paramiko.ssh_exception import NoValidConnectionsError

from exasol_integration_test_docker_environment.lib.base.ssh_access import SshKey
from exasol_integration_test_docker_environment.lib.data.database_info import (
    DatabaseInfo,
)
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient


class DockerClientFactory:
    """
    Create a Docker client.
    """

    def __init__(self, timeout: int = 100000):
        self._timeout = timeout

    def client(self) -> DockerClient:
        with ContextDockerClient(timeout=self._timeout) as client:
            return client


# Avoid TypeError: Instance and class checks can only be
# used with @runtime_checkable protocols
# raised by unit tests
@runtime_checkable
class DbOsExecutor(Protocol):
    """
    This class provides an abstraction to execute operating system
    commands on the database host, e.g. inside a Docker Container.  See
    concrete implementations in sub-classes ``DockerExecutor`` and
    ``SshExecutor``.
    """

    def exec(self, cmd: str) -> ExecResult: ...

    def prepare(self): ...


class DockerExecutor(DbOsExecutor):
    def __init__(self, docker_client: DockerClient, container_name: str):
        self._client = docker_client
        self._container_name = container_name
        self._container: Optional[Container] = None

    def __enter__(self):
        self._container = self._client.containers.get(self._container_name)
        return self

    def __exit__(self, type_, value, traceback):
        self.close()

    def __del__(self):
        self.close()

    def exec(self, cmd: str) -> ExecResult:
        assert self._container
        return self._container.exec_run(cmd)

    def prepare(self):
        pass

    def close(self):
        self._container = None
        if self._client is not None:
            self._client.close()
            self._client = None


class SshExecutor(DbOsExecutor):
    def __init__(self, connect_string: str, key_file: str):
        self._connect_string = connect_string
        self._key_file = key_file
        self._connection: Optional[fabric.Connection] = None

    def __enter__(self):
        key = SshKey.read_from(self._key_file)
        self._connection = fabric.Connection(
            self._connect_string,
            connect_kwargs={"pkey": key.private},
        )
        return self

    def __exit__(self, type_, value, traceback):
        self.close()

    def __del__(self):
        self.close()

    def exec(self, cmd: str) -> ExecResult:
        assert self._connection
        result = self._connection.run(cmd, warn=True, hide=True)
        output = result.stdout.encode("utf-8")
        return ExecResult(result.exited, output)

    def prepare(self):
        retry = 0
        while retry < 20:
            try:
                retry += 1
                self._connection.run("true", warn=True, hide=True)
                break
            except NoValidConnectionsError as ex:
                if retry > 20:
                    raise ex
                time.sleep(1)

    def close(self):
        if self._connection is not None:
            self._connection.close()
            self._connection = None


# Avoid TypeError: Instance and class checks can only be
# used with @runtime_checkable protocols
# raised by integration tests
@runtime_checkable
class DbOsExecFactory(Protocol):
    """
    This class defines an abstract method ``executor()`` to be implemented by
    inheriting factories.
    """

    @abstractmethod
    def executor(self) -> DbOsExecutor:
        """
        Create an executor for executing commands inside of the operating
        system of the database.
        """
        ...


class DockerExecFactory(DbOsExecFactory):
    def __init__(self, container_name: str, client_factory: DockerClientFactory):
        self._container_name = container_name
        self._client_factory = client_factory

    def executor(self) -> DbOsExecutor:
        client = self._client_factory.client()
        return DockerExecutor(client, self._container_name)


class SshExecFactory(DbOsExecFactory):
    @classmethod
    def from_database_info(cls, info: DatabaseInfo):
        assert info.ssh_info
        return SshExecFactory(
            f"{info.ssh_info.user}@{info.host}:{info.ports.ssh}",
            info.ssh_info.key_file,
        )

    def __init__(self, connect_string: str, ssh_key_file: str):
        self._connect_string = connect_string
        self._key_file = ssh_key_file

    def executor(self) -> DbOsExecutor:
        return SshExecutor(self._connect_string, self._key_file)
