from exasol_integration_test_docker_environment.lib.base.db_os_executor import (
    DockerExecFactory,
)
from exasol_integration_test_docker_environment.lib.test_environment.spawn_test_environment_with_docker_db import (
    SpawnTestEnvironmentWithDockerDB,
)


def test_database_readiness_always_uses_docker_exec():
    environment = object.__new__(SpawnTestEnvironmentWithDockerDB)
    environment.db_container_name = "database-container"

    factory = environment._readiness_executor_factory()

    assert isinstance(factory, DockerExecFactory)
    assert factory._container_name == "database-container"
