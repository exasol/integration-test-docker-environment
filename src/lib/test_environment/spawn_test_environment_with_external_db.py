from ...lib.test_environment.abstract_spawn_test_environment import AbstractSpawnTestEnvironment
from ...lib.data.container_info import ContainerInfo
from ...lib.data.database_info import DatabaseInfo
from ...lib.data.docker_network_info import DockerNetworkInfo
from ...lib.data.environment_type import EnvironmentType
from ...lib.test_environment.external_test_environment_parameter import ExternalDatabaseXMLRPCParameter, \
    ExternalDatabaseHostParameter
from ...lib.test_environment.prepare_network_for_test_environment import PrepareDockerNetworkForTestEnvironment
from ...lib.test_environment.setup_external_database_host import SetupExternalDatabaseHost
from ...lib.test_environment.wait_for_external_database import WaitForTestExternalDatabase


class SpawnTestEnvironmentWithExternalDB(AbstractSpawnTestEnvironment,
                                         ExternalDatabaseXMLRPCParameter,
                                         ExternalDatabaseHostParameter):

    def get_environment_type(self):
        return EnvironmentType.external_db

    def create_network_task(self, attempt: int):
        return \
            self.create_child_task_with_common_params(
                PrepareDockerNetworkForTestEnvironment,
                reuse=self.reuse_test_container,
                attempt=attempt,
                test_container_name=self.test_container_name,
                network_name=self.network_name
            )

    def create_spawn_database_task(self, network_info: DockerNetworkInfo, attempt: int):
        return \
            self.create_child_task_with_common_params(
                SetupExternalDatabaseHost,
                network_info=network_info,
                attempt=attempt
            )

    def create_wait_for_database_task(self,
                                      attempt: int,
                                      database_info: DatabaseInfo,
                                      test_container_info: ContainerInfo):
        return \
            self.create_child_task_with_common_params(
                WaitForTestExternalDatabase,
                test_container_info=test_container_info,
                database_info=database_info,
                attempt=attempt)
