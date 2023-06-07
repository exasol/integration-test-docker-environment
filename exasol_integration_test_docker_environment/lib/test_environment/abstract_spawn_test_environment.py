from pathlib import Path
from typing import Generator, Tuple, Optional

import luigi

from exasol_integration_test_docker_environment.abstract_method_exception import AbstractMethodException
from exasol_integration_test_docker_environment.lib.base.base_task import BaseTask
from exasol_integration_test_docker_environment.lib.base.docker_base_task import DockerBaseTask
from exasol_integration_test_docker_environment.lib.data.container_info import ContainerInfo
from exasol_integration_test_docker_environment.lib.data.database_credentials import DatabaseCredentialsParameter
from exasol_integration_test_docker_environment.lib.data.database_info import DatabaseInfo
from exasol_integration_test_docker_environment.lib.data.docker_network_info import DockerNetworkInfo
from exasol_integration_test_docker_environment.lib.data.docker_volume_info import DockerVolumeInfo
from exasol_integration_test_docker_environment.lib.data.environment_info import EnvironmentInfo
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

    def create_test_environment_info_in_test_container(self, test_environment_info: EnvironmentInfo,
                                                       environment_variables: str,
                                                       environment_variables_with_export: str,
                                                       json: str):
        test_container_name = test_environment_info.test_container_info.container_name
        with self._get_docker_client() as docker_client:
            test_container = docker_client.containers.get(test_container_name)
            self.logger.info(f"Create test environment info in test container '{test_container_name}' at '/'")
            copy = DockerContainerCopy(test_container)
            copy.add_string_to_file("environment_info.json", json)
            copy.add_string_to_file("environment_info.conf", environment_variables)
            copy.add_string_to_file("environment_info.sh", environment_variables_with_export)
            copy.copy("/")

    def create_test_environment_info_in_test_container_and_on_host(
            self, test_environment_info: EnvironmentInfo):
        test_environment_info_base_host_path = Path(self.get_cache_path(),
                                                    f"environments/{self.environment_name}")
        test_environment_info_base_host_path.mkdir(exist_ok=True, parents=True)
        self.logger.info(f"Create test environment info on the host at '{test_environment_info_base_host_path}'")

        json = test_environment_info.to_json()
        cache_environment_info_json_path = Path(test_environment_info_base_host_path,
                                                "environment_info.json")
        with cache_environment_info_json_path.open("w") as f:
            f.write(json)

        if test_environment_info.test_container_info is not None:
            test_container_name = test_environment_info.test_container_info.container_name
        else:
            test_container_name = ""
        environment_variables = \
            self.collect_environment_info_variables(test_container_name,
                                                    test_environment_info)
        cache_environment_info_conf_path = Path(test_environment_info_base_host_path,
                                                "environment_info.conf")
        with cache_environment_info_conf_path.open("w") as f:
            f.write(environment_variables)

        environment_variables_with_export = ""
        for line in environment_variables.splitlines():
            environment_variables_with_export += f"export {line}\n"
        cache_environment_info_sh_path = Path(test_environment_info_base_host_path, "environment_info.sh")
        with cache_environment_info_sh_path.open("w") as f:
            f.write(environment_variables_with_export)

        if test_environment_info.test_container_info is not None:
            self.create_test_environment_info_in_test_container(test_environment_info,
                                                                environment_variables,
                                                                environment_variables_with_export, json)

    def collect_environment_info_variables(self, test_container_name: str, test_environment_info):
        def default_bridge_ip_address(info):
            with self._get_docker_client() as docker_client:
                db_container = docker_client.containers.get(info.database_info.container_info.container_name)
                db_container.reload()
                return db_container.attrs["NetworkSettings"]["Networks"]["bridge"]["IPAddress"]
        info = test_environment_info
        env = {
            "NAME": info.name,
            "TYPE": info.type,
            "DATABASE_HOST": info.database_info.host,
            "DATABASE_DB_PORT": info.database_info.ports.database,
            "DATABASE_BUCKETFS_PORT": info.database_info.ports.bucketfs,
            "DATABASE_SSH_PORT": info.database_info.ports.ssh,
        }
        if info.database_info.container_info is not None:
            network_aliases = " ".join(info.database_info.container_info.network_aliases)
            env.update({
                "DATABASE_CONTAINER_NAME": info.database_info.container_info.container_name,
                "DATABASE_CONTAINER_NETWORK_ALIASES": f'"{network_aliases}"',
                "DATABASE_CONTAINER_IP_ADDRESS": info.database_info.container_info.ip_address,
                "DATABASE_CONTAINER_VOLUMNE_NAME": info.database_info.container_info.volume_name,
                "DATABASE_CONTAINER_DEFAULT_BRIDGE_IP_ADDRESS": default_bridge_ip_address(info),
            })
        if info.test_container_info is not None:
            network_aliases = " ".join(info.test_container_info.network_aliases)
            env.update({
                "TEST_CONTAINER_NAME": test_container_name,
                "TEST_CONTAINER_NETWORK_ALIASES": f'"{network_aliases}"',
                "TEST_CONTAINER_IP_ADDRESS": info.test_container_info.ip_address,
            })
        # Old implementation added an extra newline.
        # Not sure if we can remove this?
        return "\n".join([ f"ENVIRONMENT_{key}={value}" for key, value in env.items() ]) + "\n"

    def _start_database(self, attempt) \
            -> Generator[BaseTask, BaseTask, Tuple[DockerNetworkInfo, DatabaseInfo, bool, Optional[ContainerInfo]]]:
        network_info = yield from self._create_network(attempt)
        ssl_volume_info = None
        if self.create_certificates:
            ssl_volume_info = yield from self._create_ssl_certificates()
        database_info, test_container_info = \
            yield from self._spawn_database_and_test_container(network_info, ssl_volume_info, attempt)
        is_database_ready = yield from self._wait_for_database(database_info, attempt)
        return network_info, database_info, is_database_ready, test_container_info

    def _create_ssl_certificates(self) -> DockerVolumeInfo:
        ssl_info_future = yield from self.run_dependencies(self.create_ssl_certificates())
        ssl_info = self.get_values_from_future(ssl_info_future)
        return ssl_info

    def create_ssl_certificates(self):
        raise AbstractMethodException()

    def _create_network(self, attempt):
        network_info_future = yield from self.run_dependencies(self.create_network_task(attempt))
        network_info = self.get_values_from_future(network_info_future)
        return network_info

    def create_network_task(self, attempt: int):
        raise AbstractMethodException()

    def _spawn_database_and_test_container(self,
                                           network_info: DockerNetworkInfo,
                                           certificate_volume_info: Optional[DockerVolumeInfo],
                                           attempt: int) -> Tuple[DatabaseInfo, Optional[ContainerInfo]]:
        certificate_volume_name = certificate_volume_info.volume_name if certificate_volume_info is not None else None
        dependencies_tasks = {
                DATABASE: self.create_spawn_database_task(network_info, certificate_volume_info, attempt)
            }
        if self.test_container_content is not None:
            dependencies_tasks[TEST_CONTAINER] = \
                self.create_spawn_test_container_task(network_info, certificate_volume_name, attempt)
        database_and_test_container_info_future = yield from self.run_dependencies(dependencies_tasks)
        database_and_test_container_info = \
            self.get_values_from_futures(database_and_test_container_info_future)
        test_container_info = None
        if self.test_container_content is not None:
            test_container_info = database_and_test_container_info[TEST_CONTAINER]
        database_info = database_and_test_container_info[DATABASE]
        return database_info, test_container_info

    def create_spawn_database_task(self,
                                   network_info: DockerNetworkInfo,
                                   certificate_volume_info: Optional[DockerVolumeInfo],
                                   attempt: int):
        raise AbstractMethodException()

    def create_spawn_test_container_task(self, network_info: DockerNetworkInfo,
                                         certificate_volume_name: str, attempt: int):
        return self.create_child_task_with_common_params(
                SpawnTestContainer,
                test_container_name=self.test_container_name,
                network_info=network_info,
                ip_address_index_in_subnet=1,
                certificate_volume_name=certificate_volume_name,
                attempt=attempt,
                test_container_content=self.test_container_content
                )

    def _wait_for_database(self,
                           database_info: DatabaseInfo,
                           attempt: int):
        database_ready_target_future = \
            yield from self.run_dependencies(self.create_wait_for_database_task(attempt, database_info))
        is_database_ready = self.get_values_from_futures(database_ready_target_future)
        return is_database_ready

    def create_wait_for_database_task(self,
                                      attempt: int,
                                      database_info: DatabaseInfo):
        raise AbstractMethodException()
