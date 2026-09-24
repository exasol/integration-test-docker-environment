from pathlib import Path
from test.integration.get_test_container_content import (
    get_test_container_content,
)
from typing import cast
from uuid import uuid4

import luigi
import pytest

from exasol_integration_test_docker_environment.cli.options import (
    test_environment_options,
)
from exasol_integration_test_docker_environment.lib.base.run_task import (
    generate_root_task,
)
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.models.config.build_config import (
    set_build_config,
)
from exasol_integration_test_docker_environment.lib.models.config.docker_config import (
    set_docker_repository_config,
)
from exasol_integration_test_docker_environment.lib.models.data.environment_type import (
    EnvironmentType,
)
from exasol_integration_test_docker_environment.lib.test_environment.ports import Ports
from exasol_integration_test_docker_environment.lib.test_environment.spawn_test_environment import (
    SpawnTestEnvironment,
)
from exasol_integration_test_docker_environment.testing import luigi_utils
from exasol_integration_test_docker_environment.testing.utils import (
    check_db_version_from_env,
)


def _setup_luigi_config(output_directory: Path, docker_repository_name: str):
    set_build_config(
        force_rebuild=False,
        force_pull=False,
        force_rebuild_from=(),
        log_build_context_content=False,
        output_directory=str(output_directory),
        cache_directory="",
        build_name="",
        temporary_base_directory="/tmp",
    )
    set_docker_repository_config(
        docker_password=None,
        docker_repository_name=docker_repository_name,
        docker_username=None,
        tag_prefix="",
        kind="target",
    )


@pytest.fixture
def reuse_environment_name(env_name: str) -> str:
    return f"{env_name}_{uuid4().hex[:8]}"


@pytest.fixture
def docker_repository(tmp_path, reuse_environment_name):
    _setup_luigi_config(
        output_directory=tmp_path / "output",
        docker_repository_name=reuse_environment_name,
    )
    luigi_utils.clean(reuse_environment_name)
    yield reuse_environment_name
    luigi_utils.clean(reuse_environment_name)


def get_instance_ids(test_environment_info) -> tuple[str, str, str]:
    with ContextDockerClient() as docker_client:
        test_container = docker_client.containers.get(
            test_environment_info.test_container_info.container_name
        )
        db_container = docker_client.containers.get(
            test_environment_info.database_info.container_info.container_name
        )
        network = docker_client.networks.get(
            test_environment_info.network_info.network_name
        )
        return test_container.id, db_container.id, network.id


class ReusingTestEnv:
    def __init__(self, docker_repository: str, env_name: str):
        self.docker_repository = docker_repository
        self.docker_db_version_parameter = (
            check_db_version_from_env() or test_environment_options.LATEST_DB_VERSION
        )
        self.ports = Ports.random_free()
        self.env_name = env_name
        self._tasks: list[SpawnTestEnvironment] = []
        self._container_names: set[str] = set()
        self._network_names: set[str] = set()
        self._volume_names: set[str] = set()

    def cleanup(self) -> None:
        """Remove every environment created by this test, including failed runs."""
        cleanup_error = None
        try:
            for task in reversed(self._tasks):
                try:
                    task.cleanup(False)
                except Exception as error:
                    cleanup_error = cleanup_error or error
        finally:
            self._tasks.clear()
        try:
            self._assert_resources_removed()
        except Exception as error:
            cleanup_error = cleanup_error or error
        if cleanup_error:
            raise cleanup_error

    def _record_resources(self, task: SpawnTestEnvironment) -> None:
        environment = task.get_result()
        self._network_names.add(environment.network_info.network_name)
        for container_info in (
            environment.test_container_info,
            environment.database_info.container_info,
        ):
            if container_info is None:
                continue
            self._container_names.add(container_info.container_name)
            if container_info.volume_name:
                self._volume_names.add(container_info.volume_name)

    def _assert_resources_removed(self) -> None:
        with ContextDockerClient() as docker_client:
            remaining_containers = self._container_names & {
                container.name for container in docker_client.containers.list(all=True)
            }
            remaining_networks = self._network_names & {
                network.name for network in docker_client.networks.list()
            }
            remaining_volumes = self._volume_names & {
                volume.name for volume in docker_client.volumes.list()
            }
        assert not remaining_containers, f"Leaked containers: {remaining_containers}"
        assert not remaining_networks, f"Leaked networks: {remaining_networks}"
        assert not remaining_volumes, f"Leaked volumes: {remaining_volumes}"

    def run_spawn_test_env(
        self,
        cleanup: bool,
        create_confd_user: bool = False,
        include_test_container: bool = True,
    ) -> SpawnTestEnvironment:
        task = cast(
            SpawnTestEnvironment,
            generate_root_task(
                task_class=SpawnTestEnvironment,
                reuse_database_setup=True,
                reuse_database=True,
                reuse_test_container=include_test_container,
                no_test_container_cleanup_after_success=not cleanup,
                no_database_cleanup_after_success=not cleanup,
                external_exasol_db_port=self.ports.database,
                external_exasol_bucketfs_http_port=self.ports.bucketfs_http,
                external_exasol_bucketfs_https_port=self.ports.bucketfs_https,
                external_exasol_ssh_port=self.ports.ssh,
                external_exasol_xmlrpc_host="",
                external_exasol_db_host="",
                external_exasol_xmlrpc_port=0,
                external_exasol_db_user="",
                external_exasol_db_password="",
                external_exasol_xmlrpc_user="",
                external_exasol_xmlrpc_password="",
                external_exasol_xmlrpc_cluster_name="",
                external_exasol_bucketfs_write_password="",
                environment_type=EnvironmentType.docker_db,
                environment_name=self.env_name,
                docker_db_image_version=self.docker_db_version_parameter,
                docker_db_image_name="exasol/docker-db",
                test_container_content=(
                    get_test_container_content() if include_test_container else None
                ),
                create_confd_user=create_confd_user,
                additional_db_parameter=(),
                docker_environment_variables=(),
                accelerator=(),
            ),
        )
        self._tasks.append(task)
        try:
            if not luigi.build(
                [task], workers=1, local_scheduler=True, log_level="INFO"
            ):
                raise RuntimeError("Task failed")
            self._record_resources(task)
        except Exception as error:
            task.cleanup(False)
            raise RuntimeError("Error spawning test environment") from error
        return task


@pytest.fixture
def reusing_test_env(docker_repository, reuse_environment_name):
    environment = ReusingTestEnv(docker_repository, reuse_environment_name)
    try:
        yield environment
    finally:
        environment.cleanup()
