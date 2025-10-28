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
from exasol_integration_test_docker_environment.lib.models.config.build_config import set_build_config
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

ENV_NAME = "test_test_env_reuse"

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
def docker_repository(tmp_path):
    _docker_repository_name = ENV_NAME
    _setup_luigi_config(output_directory=tmp_path / "output", docker_repository_name=_docker_repository_name)
    luigi_utils.clean(_docker_repository_name)
    yield _docker_repository_name
    luigi_utils.clean(_docker_repository_name)

@pytest.fixture()
def docker_db_version_parameter():
    return check_db_version_from_env() or test_environment_options.LATEST_DB_VERSION

@pytest.fixture()
def free_ports():
    return Ports.random_free()


def run_spawn_test_env(docker_db_version_parameter, ports: Ports, cleanup: bool):
    task = generate_root_task(
        task_class=SpawnTestEnvironment,
        reuse_database_setup=True,
        reuse_database=True,
        reuse_test_container=True,
        no_test_container_cleanup_after_success=not cleanup,
        no_database_cleanup_after_success=not cleanup,
        external_exasol_db_port=ports.database,
        external_exasol_bucketfs_port=ports.bucketfs,
        external_exasol_ssh_port=ports.ssh,
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
        environment_name=ENV_NAME,
        docker_db_image_version=docker_db_version_parameter,
        docker_db_image_name="exasol/docker-db",
        test_container_content=get_test_container_content(),
        additional_db_parameter=(),
        docker_environment_variables=(),
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


def get_instance_ids(test_environment_info):
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

def test_reuse_env_same_instances(docker_repository, docker_db_version_parameter, free_ports):
    """
    This test spawns a new test environment and, with parameters:
    * reuse_database_setup=True,
    * reuse_database=True,
    * reuse_test_container=True
    and verifies if the test data was populated to the docker db.
    """
    task = run_spawn_test_env(docker_db_version_parameter=docker_db_version_parameter, ports=free_ports, cleanup=False)
    test_environment_info = task.get_result()
    old_instance_ids = get_instance_ids(test_environment_info)
    # This clean is supposed to not remove docker instances
    task.cleanup(True)

    task = run_spawn_test_env(docker_db_version_parameter=docker_db_version_parameter, ports=free_ports, cleanup=True)
    test_environment_info = task.get_result()
    new_instance_ids = get_instance_ids(test_environment_info)
    assert old_instance_ids == new_instance_ids

    task.cleanup(True)

