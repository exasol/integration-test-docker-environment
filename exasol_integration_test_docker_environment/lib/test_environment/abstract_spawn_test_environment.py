from pathlib import Path
from typing import Generator, Tuple

import luigi

from exasol_integration_test_docker_environment.abstract_method_exception import AbstractMethodException
from exasol_integration_test_docker_environment.lib.base.base_task import BaseTask
from exasol_integration_test_docker_environment.lib.base.docker_base_task import DockerBaseTask
from exasol_integration_test_docker_environment.lib.data.container_info import ContainerInfo
from exasol_integration_test_docker_environment.lib.data.database_credentials import DatabaseCredentialsParameter
from exasol_integration_test_docker_environment.lib.data.database_info import DatabaseInfo
from exasol_integration_test_docker_environment.lib.data.docker_network_info import DockerNetworkInfo
from exasol_integration_test_docker_environment.lib.data.environment_info import EnvironmentInfo
from exasol_integration_test_docker_environment.lib.test_environment.database_setup.populate_data import \
    PopulateEngineSmallTestDataToDatabase
from exasol_integration_test_docker_environment.lib.test_environment.database_setup.upload_exa_jdbc import UploadExaJDBC
from exasol_integration_test_docker_environment.lib.test_environment.database_setup.upload_virtual_schema_jdbc_adapter import \
    UploadVirtualSchemaJDBCAdapter
from exasol_integration_test_docker_environment.lib.test_environment.docker_container_copy import DockerContainerCopy
from exasol_integration_test_docker_environment.lib.test_environment.parameter.general_spawn_test_environment_parameter import \
    GeneralSpawnTestEnvironmentParameter
from exasol_integration_test_docker_environment.lib.test_environment.spawn_test_container import SpawnTestContainer

DATABASE = "database"

TEST_CONTAINER = "test_container"


class AbstractSpawnTestEnvironment(DockerBaseTask,
                                   GeneralSpawnTestEnvironmentParameter,
                                   DatabaseCredentialsParameter):
    environment_name = luigi.Parameter()  # type: str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_container_name = f"""test_container_{self.environment_name}"""
        self.network_name = f"""db_network_{self.environment_name}"""

    def get_environment_type(self):
        raise AbstractMethodException()

    def run_task(self):
        test_environment_info = yield from self._attempt_database_start()
        yield from self._setup_test_database(test_environment_info)
        self.return_object(test_environment_info)

    def _attempt_database_start(self):
        is_database_ready = False
        attempt = 0
        database_info = None
        test_container_info = None
        while not is_database_ready and attempt < self.max_start_attempts:
            network_info, database_info, is_database_ready, test_container_info = \
                yield from self._start_database(attempt)
            attempt += 1
        if not is_database_ready and not attempt < self.max_start_attempts:
            raise Exception(f"Maximum attempts {attempt} to start the database reached.")
        test_environment_info = \
            EnvironmentInfo(name=self.environment_name,
                            env_type=self.get_environment_type(),
                            database_info=database_info,
                            test_container_info=test_container_info,
                            network_info=network_info)
        self.create_test_environment_info_in_test_container_and_on_host(test_environment_info)
        return test_environment_info

    def create_test_environment_info_in_test_container_and_on_host(
            self, test_environment_info: EnvironmentInfo):
        test_container_name = test_environment_info.test_container_info.container_name
        with self._get_docker_client() as docker_client:
            test_container = docker_client.containers.get(test_container_name)
            test_environment_info_base_host_path = Path(self.get_cache_path(),
                                                        f"environments/{self.environment_name}")
            test_environment_info_base_host_path.mkdir(exist_ok=True, parents=True)
            self.logger.info(
                f"Create test environment info in test container '{test_container_name}' at '/' "
                f"and on the host at '{test_environment_info_base_host_path}'")

            copy = DockerContainerCopy(test_container)
            json = test_environment_info.to_json()
            copy.add_string_to_file("environment_info.json", json)
            cache_environment_info_json_path = Path(test_environment_info_base_host_path,
                                                    "environment_info.json")
            with cache_environment_info_json_path.open("w") as f:
                f.write(json)

            environment_variables = \
                self.collect_environment_info_variables(test_container_name,
                                                        test_environment_info)
            copy.add_string_to_file("environment_info.conf", environment_variables)
            cache_environment_info_conf_path = Path(test_environment_info_base_host_path,
                                                    "environment_info.conf")
            with cache_environment_info_conf_path.open("w") as f:
                f.write(environment_variables)

            environment_variables_with_export = ""
            for line in environment_variables.splitlines():
                environment_variables_with_export += f"export {line}\n"
            copy.add_string_to_file("environment_info.sh", environment_variables_with_export)
            cache_environment_info_sh_path = Path(test_environment_info_base_host_path, "environment_info.sh")
            with cache_environment_info_sh_path.open("w") as f:
                f.write(environment_variables_with_export)

            copy.copy("/")

    def collect_environment_info_variables(self, test_container_name, test_environment_info):
        environment_variables = ""
        environment_variables += f"ENVIRONMENT_NAME={test_environment_info.name}\n"
        environment_variables += f"ENVIRONMENT_TYPE={test_environment_info.type}\n"
        environment_variables += f"ENVIRONMENT_DATABASE_HOST={test_environment_info.database_info.host}\n"
        environment_variables += f"ENVIRONMENT_DATABASE_DB_PORT={test_environment_info.database_info.db_port}\n"
        environment_variables += f"ENVIRONMENT_DATABASE_BUCKETFS_PORT={test_environment_info.database_info.bucketfs_port}\n"
        if test_environment_info.database_info.container_info is not None:
            environment_variables += f"""ENVIRONMENT_DATABASE_CONTAINER_NAME={test_environment_info.database_info.container_info.container_name}\n"""
            database_container_network_aliases = " ".join(
                test_environment_info.database_info.container_info.network_aliases)
            environment_variables += f"""ENVIRONMENT_DATABASE_CONTAINER_NETWORK_ALIASES="{database_container_network_aliases}"\n"""
            environment_variables += f"""ENVIRONMENT_DATABASE_CONTAINER_IP_ADDRESS={test_environment_info.database_info.container_info.ip_address}\n"""
            environment_variables += f"""ENVIRONMENT_DATABASE_CONTAINER_VOLUMNE_NAME={test_environment_info.database_info.container_info.volume_name}\n"""
            with self._get_docker_client() as docker_client:
                db_container = docker_client.containers.get(
                    test_environment_info.database_info.container_info.container_name)
                db_container.reload()
                default_bridge_ip_address = db_container.attrs["NetworkSettings"]["Networks"]["bridge"]["IPAddress"]
            environment_variables += f"""ENVIRONMENT_DATABASE_CONTAINER_DEFAULT_BRIDGE_IP_ADDRESS={default_bridge_ip_address}\n"""
        if test_environment_info.test_container_info is not None:
            environment_variables += f"""ENVIRONMENT_TEST_CONTAINER_NAME={test_container_name}\n"""
            test_container_network_aliases = " ".join(test_environment_info.test_container_info.network_aliases)
            environment_variables += f"""ENVIRONMENT_TEST_CONTAINER_NETWORK_ALIASES="{test_container_network_aliases}"\n"""
            environment_variables += f"""ENVIRONMENT_TEST_CONTAINER_IP_ADDRESS={test_environment_info.test_container_info.ip_address}\n"""
        return environment_variables

    def _start_database(self, attempt) \
            -> Generator[BaseTask, BaseTask, Tuple[DockerNetworkInfo, DatabaseInfo, bool, ContainerInfo]]:
        network_info = yield from self._create_network(attempt)
        database_info, test_container_info = \
            yield from self._spawn_database_and_test_container(network_info, attempt)
        is_database_ready = yield from self._wait_for_database(
            database_info, test_container_info, attempt)
        return network_info, database_info, is_database_ready, test_container_info

    def _create_network(self, attempt):
        network_info_future = yield from self.run_dependencies(self.create_network_task(attempt))
        network_info = self.get_values_from_future(network_info_future)
        return network_info

    def create_network_task(self, attempt: int):
        raise AbstractMethodException()

    def _spawn_database_and_test_container(self,
                                           network_info: DockerNetworkInfo,
                                           attempt: int):
        database_and_test_container_info_future = \
            yield from self.run_dependencies({
                TEST_CONTAINER: \
                    self.create_child_task_with_common_params(
                        SpawnTestContainer,
                        test_container_name=self.test_container_name,
                        network_info=network_info,
                        ip_address_index_in_subnet=1,
                        attempt=attempt),
                DATABASE: self.create_spawn_database_task(network_info, attempt)
            })
        database_and_test_container_info = \
            self.get_values_from_futures(database_and_test_container_info_future)
        test_container_info = database_and_test_container_info[TEST_CONTAINER]
        database_info = database_and_test_container_info[DATABASE]
        return database_info, test_container_info

    def create_spawn_database_task(self,
                                   network_info: DockerNetworkInfo,
                                   attempt: int):
        raise AbstractMethodException()

    def _wait_for_database(self,
                           database_info: DatabaseInfo,
                           test_container_info: ContainerInfo,
                           attempt: int):
        database_ready_target_future = \
            yield from self.run_dependencies(
                self.create_wait_for_database_task(
                    attempt, database_info, test_container_info))
        is_database_ready = self.get_values_from_futures(database_ready_target_future)
        return is_database_ready

    def create_wait_for_database_task(self,
                                      attempt: int,
                                      database_info: DatabaseInfo,
                                      test_container_info: ContainerInfo):
        raise AbstractMethodException()

    def _setup_test_database(self, test_environment_info: EnvironmentInfo):
        # TODO check if database is setup
        if self.is_setup_database_activated:
            self.logger.info("Setup database")
            upload_tasks = [
                self.create_child_task_with_common_params(
                    UploadExaJDBC,
                    test_environment_info=test_environment_info,
                    reuse_uploaded=self.reuse_database_setup),
                self.create_child_task_with_common_params(
                    UploadVirtualSchemaJDBCAdapter,
                    test_environment_info=test_environment_info,
                    reuse_uploaded=self.reuse_database_setup),
                self.create_child_task_with_common_params(
                    PopulateEngineSmallTestDataToDatabase,
                    test_environment_info=test_environment_info,
                    reuse_data=self.reuse_database_setup
                )]
            yield from self.run_dependencies(upload_tasks)
