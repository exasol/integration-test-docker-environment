from pathlib import Path

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
from exasol_integration_test_docker_environment.test.get_test_container_content import (
    get_test_container_content,
)
from exasol_integration_test_docker_environment.testing import luigi_utils
from exasol_integration_test_docker_environment.testing.utils import (
    check_db_version_from_env,
)


@pytest.fixture()
def env_name(request):
    return request.node.name


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


@pytest.fixture()
def docker_repository(tmp_path, env_name):
    _docker_repository_name = env_name
    _setup_luigi_config(
        output_directory=tmp_path / "output",
        docker_repository_name=_docker_repository_name,
    )
    luigi_utils.clean(_docker_repository_name)
    yield _docker_repository_name
    luigi_utils.clean(_docker_repository_name)


def _get_instance_ids(test_environment_info) -> tuple[str, str, str]:
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

    def __init__(self, docker_repository, env_name):
        self.docker_repository = docker_repository
        self.docker_db_version_parameter = (
            check_db_version_from_env() or test_environment_options.LATEST_DB_VERSION
        )
        self.ports = Ports.random_free()
        self.env_name = env_name

    def run(self, cleanup: bool) -> tuple[str, str, str]:
        task = self.run_spawn_test_env(
            cleanup=cleanup,
        )
        try:
            env_info = task.get_result()

            ids = _get_instance_ids(env_info)
            task_success = (
                not cleanup
            )  # Calling task.cleanup(False) will remove container/network/volume, while task.cleanup(True) will not
            task.cleanup(task_success)
        except Exception as e:
            task.cleanup(False)
            raise e
        return ids

    def run_spawn_test_env(self, cleanup: bool):
        no_cleanup_after_success = not cleanup
        task = generate_root_task(
            task_class=SpawnTestEnvironment,
            reuse_database_setup=True,
            reuse_database=True,
            reuse_test_container=True,
            no_test_container_cleanup_after_success=no_cleanup_after_success,
            no_database_cleanup_after_success=no_cleanup_after_success,
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
            test_container_content=get_test_container_content(),
            additional_db_parameter=(),
            docker_environment_variables=(),
            accelerator=(),
        )
        try:
            success = luigi.build(
                [task], workers=1, local_scheduler=True, log_level="INFO"
            )
            if success:
                result = task
            else:
                raise Exception("Task failed")
        except Exception as e:
            task.cleanup(False)
            raise RuntimeError("Error spawning test environment") from e
        return result


@pytest.fixture
def reusing_test_env(docker_repository, env_name) -> ReusingTestEnv:
    return ReusingTestEnv(docker_repository, env_name)


def test_reuse_instances(reusing_test_env: ReusingTestEnv):
    """
    This test uses a test environment, configured to reuse the test
    container, DB setup and the database, see function run_spawn_test_env()
    above.
    The test spawns the environment with cleanup=False and extracts the IDs of
    the environment's elements test container, database, and network.
    The test then spawns another environment and verifies that the elements
    have been reused, i.e. their IDs match the save ones from before.
    """
    old_ids = reusing_test_env.run(cleanup=False)
    new_ids = reusing_test_env.run(cleanup=True)
    assert new_ids == old_ids
