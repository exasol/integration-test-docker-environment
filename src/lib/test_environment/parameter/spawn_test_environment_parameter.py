import luigi

from src.lib.data.environment_type import EnvironmentType
from src.lib.test_environment.parameter.docker_db_test_environment_parameter import DockerDBTestEnvironmentParameter
from src.lib.test_environment.parameter.external_test_environment_parameter import ExternalDatabaseCredentialsParameter
from src.lib.test_environment.parameter.general_spawn_test_environment_parameter import \
    GeneralSpawnTestEnvironmentParameter


class SpawnTestEnvironmentParameter(GeneralSpawnTestEnvironmentParameter,
                                    ExternalDatabaseCredentialsParameter,
                                    DockerDBTestEnvironmentParameter):
    environment_type = luigi.EnumParameter(enum=EnvironmentType)
