from pathlib import Path
from test.integration.get_test_container_content import (
    get_test_container_content,
)

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

    def run_spawn_test_env(
        self,
        cleanup: bool,
        create_confd_user: bool = False,
        include_test_container: bool = True,
    ):
        no_cleanup_after_success = not cleanup
        task = generate_root_task(
            task_class=SpawnTestEnvironment,
            reuse_database_setup=True,
            reuse_database=True,
            reuse_test_container=include_test_container,
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
            test_container_content=(
                get_test_container_content() if include_test_container else None
            ),
            create_confd_user=create_confd_user,
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


def test_reuse_returns_existing_confd_credentials(reusing_test_env: ReusingTestEnv):
    """Reuse a Docker-DB ConfD account without recreating or changing it."""
    first_task = reusing_test_env.run_spawn_test_env(
        cleanup=False, create_confd_user=True, include_test_container=False
    )
    second_task = None
    try:
        first_environment = first_task.get_result()
        first_confd_info = first_environment.database_info.confd_info
        assert first_confd_info is not None
        first_credentials_file = Path(first_confd_info.credentials_file)
        assert first_credentials_file.exists()
        first_credentials = first_confd_info.read_credentials()

        # Keep the first database and its owner-only credentials file for reuse.
        first_task.cleanup(True)

        second_task = reusing_test_env.run_spawn_test_env(
            cleanup=True, create_confd_user=True, include_test_container=False
        )
        second_environment = second_task.get_result()
        second_confd_info = second_environment.database_info.confd_info
        assert second_confd_info is not None

        assert second_environment.database_info.reused
        assert second_confd_info.credentials_file == str(first_credentials_file)
        assert (
            second_confd_info.read_credentials().password == first_credentials.password
        )
    finally:
        if second_task is not None:
            second_task.cleanup(False)
        else:
            first_task.cleanup(False)


def test_reuse_repairs_missing_confd_credentials(reusing_test_env: ReusingTestEnv):
    """Reuse repairs a deleted local ConfD credentials file and rotates its secret."""
    first_task = reusing_test_env.run_spawn_test_env(
        cleanup=False, create_confd_user=True, include_test_container=False
    )
    second_task = None
    try:
        first_environment = first_task.get_result()
        first_confd_info = first_environment.database_info.confd_info
        assert first_confd_info is not None
        credentials_file = Path(first_confd_info.credentials_file)
        first_password = first_confd_info.read_credentials().password

        # Keep the database but emulate loss of local task-cache state.
        first_task.cleanup(True)
        credentials_file.unlink()

        second_task = reusing_test_env.run_spawn_test_env(
            cleanup=True, create_confd_user=True, include_test_container=False
        )
        second_environment = second_task.get_result()
        second_confd_info = second_environment.database_info.confd_info
        assert second_confd_info is not None

        assert second_environment.database_info.reused
        assert second_confd_info.credentials_file == str(credentials_file)
        assert credentials_file.exists()
        assert second_confd_info.read_credentials().password != first_password
    finally:
        if second_task is not None:
            second_task.cleanup(False)
        else:
            first_task.cleanup(False)


def test_reuse_fails_when_missing_credentials_cannot_be_repaired(
    reusing_test_env: ReusingTestEnv,
):
    """Reuse fails without recreating local credentials when ConfD is unavailable."""
    first_task = reusing_test_env.run_spawn_test_env(
        cleanup=False, create_confd_user=True, include_test_container=False
    )
    try:
        first_environment = first_task.get_result()
        first_confd_info = first_environment.database_info.confd_info
        database_container_info = first_environment.database_info.container_info
        assert first_confd_info is not None
        assert database_container_info is not None
        credentials_file = Path(first_confd_info.credentials_file)

        # Keep the database container running but remove the local credentials
        # and make its ConfD client unavailable. Both repair alternatives must
        # then fail, without writing a new credentials file.
        first_task.cleanup(True)
        credentials_file.unlink()
        with ContextDockerClient() as docker_client:
            database_container = docker_client.containers.get(
                database_container_info.container_name
            )
            exit_code, _ = database_container.exec_run(
                [
                    "/bin/sh",
                    "-c",
                    'confd_client_path="$(command -v confd_client)" || exit 1; '
                    'chmod a-x "$confd_client_path"',
                ],
                environment={
                    "CONFD_HOST": first_environment.database_info.host,
                    "HOSTNAME": "localhost",
                },
            )
        assert exit_code == 0

        with pytest.raises(RuntimeError, match="Error spawning test environment"):
            reusing_test_env.run_spawn_test_env(
                cleanup=True, create_confd_user=True, include_test_container=False
            )

        assert not credentials_file.exists()
    finally:
        first_task.cleanup(False)
