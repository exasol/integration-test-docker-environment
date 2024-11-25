from pathlib import Path
from typing import (
    Any,
    Generator,
    Optional,
    Tuple,
)

import luigi

from exasol_integration_test_docker_environment.abstract_method_exception import (
    AbstractMethodException,
)
from exasol_integration_test_docker_environment.lib.base.base_task import BaseTask
from exasol_integration_test_docker_environment.lib.base.docker_base_task import (
    DockerBaseTask,
)
from exasol_integration_test_docker_environment.lib.data.container_info import (
    ContainerInfo,
)
from exasol_integration_test_docker_environment.lib.data.database_credentials import (
    DatabaseCredentialsParameter,
)
from exasol_integration_test_docker_environment.lib.data.database_info import (
    DatabaseInfo,
)
from exasol_integration_test_docker_environment.lib.data.docker_network_info import (
    DockerNetworkInfo,
)
from exasol_integration_test_docker_environment.lib.data.docker_volume_info import (
    DockerVolumeInfo,
)
from exasol_integration_test_docker_environment.lib.data.environment_info import (
    EnvironmentInfo,
)
from exasol_integration_test_docker_environment.lib.docker.container.utils import (
    default_bridge_ip_address,
)
from exasol_integration_test_docker_environment.lib.test_environment.docker_container_copy import (
    DockerContainerCopy,
)
from exasol_integration_test_docker_environment.lib.test_environment.parameter.general_spawn_test_environment_parameter import (
    GeneralSpawnTestEnvironmentParameter,
)
from exasol_integration_test_docker_environment.lib.test_environment.shell_variables import (
    ShellVariables,
)
from exasol_integration_test_docker_environment.lib.test_environment.spawn_test_container import (
    SpawnTestContainer,
)

DATABASE = "database"

TEST_CONTAINER = "test_container"


class AbstractSpawnTestEnvironment(
    DockerBaseTask, GeneralSpawnTestEnvironmentParameter, DatabaseCredentialsParameter
):
    environment_name: str = luigi.Parameter()  # type: ignore

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
            network_info, database_info, is_database_ready, test_container_info = (
                yield from self._start_database(attempt)
            )
            attempt += 1
        if not is_database_ready and not attempt < self.max_start_attempts:
            raise Exception(
                f"Maximum attempts {attempt} to start the database reached."
            )
        test_environment_info = EnvironmentInfo(
            name=self.environment_name,
            env_type=self.get_environment_type(),
            database_info=database_info,
            test_container_info=test_container_info,
            network_info=network_info,
        )
        self.create_test_environment_info_in_test_container_and_on_host(
            test_environment_info
        )
        return test_environment_info

    def create_test_environment_info_in_test_container(
        self,
        test_environment_info: EnvironmentInfo,
        shell_variables: ShellVariables,
        json: str,
    ):
        assert test_environment_info.test_container_info
        test_container_name = test_environment_info.test_container_info.container_name
        with self._get_docker_client() as docker_client:
            test_container = docker_client.containers.get(test_container_name)
            self.logger.info(
                f"Create test environment info in test container '{test_container_name}' at '/'"
            )
            copy = DockerContainerCopy(test_container)
            copy.add_string_to_file("environment_info.json", json)
            copy.add_string_to_file("environment_info.conf", shell_variables.render())
            copy.add_string_to_file(
                "environment_info.sh", shell_variables.render("export ")
            )
            copy.copy("/")

    def create_test_environment_info_in_test_container_and_on_host(
        self, test_environment_info: EnvironmentInfo
    ):
        path = Path(self.get_cache_path(), f"environments/{self.environment_name}")
        path.mkdir(exist_ok=True, parents=True)
        self.logger.info(f"Create test environment info on the host at '{path}'")

        json = test_environment_info.to_json()
        with Path(path, "environment_info.json").open("w") as f:
            f.write(json)

        shell_variables = self.collect_shell_variables(test_environment_info)
        with Path(path, "environment_info.conf").open("w") as f:
            f.write(shell_variables.render())

        with Path(path, "environment_info.sh").open("w") as f:
            f.write(shell_variables.render("export "))

        if test_environment_info.test_container_info is not None:
            self.create_test_environment_info_in_test_container(
                test_environment_info,
                shell_variables,
                json,
            )

    def _default_bridge_ip_address(self, test_environment_info) -> Optional[str]:
        if test_environment_info.database_info.container_info is not None:
            container_name = (
                test_environment_info.database_info.container_info.container_name
            )
            with self._get_docker_client() as docker_client:
                db_container = docker_client.containers.get(container_name)
                return default_bridge_ip_address(db_container)
        return None

    def collect_shell_variables(self, test_environment_info) -> ShellVariables:
        return ShellVariables.from_test_environment_info(
            self._default_bridge_ip_address(test_environment_info),
            test_environment_info,
        )

    def _start_database(
        self, attempt
    ) -> Generator[
        Any, None, Tuple[DockerNetworkInfo, DatabaseInfo, bool, Optional[ContainerInfo]]
    ]:
        network_info = yield from self._create_network(attempt)
        ssl_volume_info = None
        if self.create_certificates:
            ssl_volume_info = yield from self._create_ssl_certificates()
        database_info, test_container_info = (
            yield from self._spawn_database_and_test_container(
                network_info, ssl_volume_info, attempt
            )
        )
        is_database_ready = yield from self._wait_for_database(database_info, attempt)
        return network_info, database_info, is_database_ready, test_container_info

    def _create_ssl_certificates(
        self,
    ) -> Generator[BaseTask, None, Optional[DockerVolumeInfo]]:
        ssl_volume_info_future = yield from self.run_dependencies(
            self.create_ssl_certificates()
        )
        ssl_volume_info: Optional[DockerVolumeInfo] = self.get_values_from_future(ssl_volume_info_future)  # type: ignore
        return ssl_volume_info

    def create_ssl_certificates(self):
        raise AbstractMethodException()

    def _create_network(self, attempt):
        network_info_future = yield from self.run_dependencies(
            self.create_network_task(attempt)
        )
        network_info = self.get_values_from_future(network_info_future)
        return network_info

    def create_network_task(self, attempt: int):
        raise AbstractMethodException()

    def _spawn_database_and_test_container(
        self,
        network_info: DockerNetworkInfo,
        certificate_volume_info: Optional[DockerVolumeInfo],
        attempt: int,
    ) -> Generator[BaseTask, None, Tuple[DatabaseInfo, Optional[ContainerInfo]]]:
        def volume_name(info):
            return None if info is None else info.volume_name

        child_tasks = {
            DATABASE: self.create_spawn_database_task(
                network_info,
                certificate_volume_info,
                attempt,
            )
        }
        if self.test_container_content is not None:
            certificate_volume_name = volume_name(certificate_volume_info)
            child_tasks[TEST_CONTAINER] = self.create_spawn_test_container_task(
                network_info,
                certificate_volume_name,
                attempt,
            )
        futures = yield from self.run_dependencies(child_tasks)
        results = self.get_values_from_futures(futures)
        database_info: DatabaseInfo = results[DATABASE]  # type: ignore
        test_container_info: Optional[ContainerInfo] = results[TEST_CONTAINER] if self.test_container_content is not None else None  # type: ignore
        return database_info, test_container_info

    def create_spawn_database_task(
        self,
        network_info: DockerNetworkInfo,
        certificate_volume_info: Optional[DockerVolumeInfo],
        attempt: int,
    ):
        raise AbstractMethodException()

    def create_spawn_test_container_task(
        self,
        network_info: DockerNetworkInfo,
        certificate_volume_name: str,
        attempt: int,
    ):
        return self.create_child_task_with_common_params(
            SpawnTestContainer,
            test_container_name=self.test_container_name,
            network_info=network_info,
            ip_address_index_in_subnet=1,
            certificate_volume_name=certificate_volume_name,
            attempt=attempt,
            test_container_content=self.test_container_content,
        )

    def _wait_for_database(self, database_info: DatabaseInfo, attempt: int):
        database_ready_target_future = yield from self.run_dependencies(
            self.create_wait_for_database_task(attempt, database_info)
        )
        is_database_ready = self.get_values_from_futures(database_ready_target_future)
        return is_database_ready

    def create_wait_for_database_task(self, attempt: int, database_info: DatabaseInfo):
        raise AbstractMethodException()
