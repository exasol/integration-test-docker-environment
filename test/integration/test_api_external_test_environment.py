from typing import List

import pytest

from exasol_integration_test_docker_environment.lib.base.run_task import (
    generate_root_task,
    run_task,
)
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.docker.container.utils import (
    remove_docker_container,
)
from exasol_integration_test_docker_environment.lib.models.data.environment_info import (
    EnvironmentInfo,
)
from exasol_integration_test_docker_environment.lib.models.data.environment_type import (
    EnvironmentType,
)
from exasol_integration_test_docker_environment.lib.test_environment.spawn_test_environment import (
    SpawnTestEnvironment,
)
from exasol_integration_test_docker_environment.test.get_test_container_content import (
    get_test_container_content,
)

def find_docker_containers(search_pattern: str) -> List[str]:
    with ContextDockerClient() as docker_client:
        containers = [
            c.name
            for c in docker_client.containers.list()
            if search_pattern in c.name
        ]
        return containers

@pytest.fixture(scope="module")
def spawn_test_environment(request, api_database_module, api_isolation_module):
    with api_database_module() as db:
        ext_environment_name = request.module.__name__
        task_creator = lambda: generate_root_task(
            task_class=SpawnTestEnvironment,
            environment_type=EnvironmentType.external_db,
            environment_name=ext_environment_name,
            external_exasol_db_host=db.database_host,
            external_exasol_db_port=db.ports.database,
            external_exasol_bucketfs_port=db.ports.bucketfs,
            external_exasol_ssh_port=db.ports.ssh,
            external_exasol_db_user=db.db_username,
            external_exasol_db_password=db.db_password,
            external_exasol_bucketfs_write_password=db.bucketfs_password,
            external_exasol_xmlrpc_host=None,
            external_exasol_xmlrpc_port=443,
            external_exasol_xmlrpc_user="admin",
            external_exasol_xmlrpc_password=None,
            external_exasol_xmlrpc_cluster_name="cluster1",
            no_test_container_cleanup_after_success=True,
            no_test_container_cleanup_after_failure=False,
            reuse_test_container=True,
            test_container_content=get_test_container_content(),
            additional_db_parameter=tuple(),
            docker_environment_variables=tuple(),
        )
        ext_environment_info: EnvironmentInfo = run_task(task_creator, 1, None)
        yield ext_environment_name, ext_environment_info, db.name

        containers = find_docker_containers(ext_environment_name)
        remove_docker_container(containers)


def test_external_db(spawn_test_environment):
    ext_environment_name, _, docker_environment_name = spawn_test_environment
    db_containers = find_docker_containers(docker_environment_name)
    test_containers = find_docker_containers(ext_environment_name)
    assert len(db_containers) == 1, f"Not exactly 1 containers in {db_containers}."
    db_container = [c for c in db_containers if "db_container" in c]
    assert len(db_container) == 1, f"Found no db container in {db_containers}."
    assert len(test_containers) == 1, f"Not exactly 1 containers in {test_containers}."
    test_container = [c for c in test_containers if "test_container" in c]
    assert len(test_container) == 1, f"Found no test container in {test_containers}."


def test_docker_available_in_test_container(spawn_test_environment):
    _, ext_environment_info, _ = spawn_test_environment
    with ContextDockerClient() as docker_client:
        test_container = docker_client.containers.get(
            ext_environment_info.test_container_info.container_name
        )
        exit_result = test_container.exec_run("docker ps")
        exit_code = exit_result[0]
        output = exit_result[1]
        assert (
            exit_code == 0
        ), f"Error while executing 'docker ps' in test container got output\n {output}."
