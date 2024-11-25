from typing import Optional

from exasol_integration_test_docker_environment.lib.data.database_info import (
    DatabaseInfo,
)
from exasol_integration_test_docker_environment.lib.data.docker_network_info import (
    DockerNetworkInfo,
)
from exasol_integration_test_docker_environment.lib.data.docker_volume_info import (
    DockerVolumeInfo,
)
from exasol_integration_test_docker_environment.lib.data.environment_type import (
    EnvironmentType,
)
from exasol_integration_test_docker_environment.lib.test_environment.abstract_spawn_test_environment import (
    AbstractSpawnTestEnvironment,
)
from exasol_integration_test_docker_environment.lib.test_environment.database_waiters.wait_for_external_database import (
    WaitForTestExternalDatabase,
)
from exasol_integration_test_docker_environment.lib.test_environment.parameter.external_test_environment_parameter import (
    ExternalDatabaseHostParameter,
    ExternalDatabaseXMLRPCParameter,
)
from exasol_integration_test_docker_environment.lib.test_environment.prepare_network_for_test_environment import (
    PrepareDockerNetworkForTestEnvironment,
)
from exasol_integration_test_docker_environment.lib.test_environment.setup_external_database_host import (
    SetupExternalDatabaseHost,
)


class SpawnTestEnvironmentWithExternalDB(
    AbstractSpawnTestEnvironment,
    ExternalDatabaseXMLRPCParameter,
    ExternalDatabaseHostParameter,
):

    def get_environment_type(self):
        return EnvironmentType.external_db

    def create_network_task(self, attempt: int):
        return self.create_child_task_with_common_params(
            PrepareDockerNetworkForTestEnvironment,
            reuse=self.reuse_test_container,
            attempt=attempt,
            test_container_name=self.test_container_name,
            network_name=self.network_name,
            no_cleanup_after_success=self.reuse_test_container,
            no_cleanup_after_failure=self.reuse_test_container,
        )

    def create_spawn_database_task(
        self,
        network_info: DockerNetworkInfo,
        certificate_volume_info: Optional[DockerVolumeInfo],
        attempt: int,
    ):
        if certificate_volume_info is not None:
            raise ValueError(
                "Certificate volume must be None when using external database"
            )

        return self.create_child_task_with_common_params(
            SetupExternalDatabaseHost, network_info=network_info, attempt=attempt
        )

    def create_wait_for_database_task(self, attempt: int, database_info: DatabaseInfo):
        return self.create_child_task_with_common_params(
            WaitForTestExternalDatabase, database_info=database_info, attempt=attempt
        )
