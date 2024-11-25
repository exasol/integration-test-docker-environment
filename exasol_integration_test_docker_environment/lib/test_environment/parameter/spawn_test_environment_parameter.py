import luigi

from exasol_integration_test_docker_environment.lib.data.environment_type import (
    EnvironmentType,
)
from exasol_integration_test_docker_environment.lib.test_environment.parameter.docker_db_test_environment_parameter import (
    DockerDBTestEnvironmentParameter,
)
from exasol_integration_test_docker_environment.lib.test_environment.parameter.external_test_environment_parameter import (
    ExternalDatabaseCredentialsParameter,
)
from exasol_integration_test_docker_environment.lib.test_environment.parameter.general_spawn_test_environment_parameter import (
    GeneralSpawnTestEnvironmentParameter,
)


class SpawnTestEnvironmentParameter(
    GeneralSpawnTestEnvironmentParameter,
    ExternalDatabaseCredentialsParameter,
    DockerDBTestEnvironmentParameter,
):
    environment_type = luigi.EnumParameter(enum=EnvironmentType)
