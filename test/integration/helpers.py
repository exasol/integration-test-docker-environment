import contextlib
import re
from typing import Any, Union, cast
from unittest.mock import Mock

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment \
    .lib.test_environment.parameter.docker_db_test_environment_parameter \
    import DbOsAccess
from exasol_integration_test_docker_environment.lib.base.db_os_executor import (
    SshExecFactory,
    DockerExecFactory,
    DbOsExecFactory,
    DockerClientFactory,
)
from exasol_integration_test_docker_environment.lib.data.database_info \
    import DatabaseInfo


def normalize_request_name(name: str):
    name = re.sub(r"[\[\]._]+", "_", name)
    return re.sub(r"^_+|_+$", "", name)


def exact_matcher(names):
    return lambda value: all(x == value for x in names)


def superset_matcher(names):
    return lambda value: all(x in value for x in names)

@contextlib.contextmanager
def container_named(*names, matcher=None):
    matcher = matcher if matcher else exact_matcher(names)
    with ContextDockerClient() as client:
        matches = [c for c in client.containers.list() if matcher(c.name)]
        yield matches[0] if matches else None


def get_executor_factory(
    dbinfo: DatabaseInfo,
    db_os_access: DbOsAccess = DbOsAccess.DOCKER_EXEC,
) -> DbOsExecFactory:
    if db_os_access == DbOsAccess.SSH:
        return SshExecFactory.from_database_info(dbinfo)
    client_factory = DockerClientFactory(timeout=100000)
    return DockerExecFactory(dbinfo.container_info.container_name, client_factory)


def mock_cast(obj: Any) -> Mock:
    return cast(Mock, obj)
