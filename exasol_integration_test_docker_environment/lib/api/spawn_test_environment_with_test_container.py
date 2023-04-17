import functools
from typing import Tuple, Optional, Callable
import humanfriendly

from exasol_integration_test_docker_environment.lib.api.common import set_build_config, set_docker_repository_config, \
    run_task, generate_root_task, no_cli_function
from exasol_integration_test_docker_environment.cli.options.docker_repository_options import \
    DEFAULT_DOCKER_REPOSITORY_NAME
from exasol_integration_test_docker_environment.cli.options.system_options import DEFAULT_OUTPUT_DIRECTORY
from exasol_integration_test_docker_environment.cli.options.test_environment_options import LATEST_DB_VERSION
from exasol_integration_test_docker_environment.lib.api.api_errors import ArgumentConstraintError
from exasol_integration_test_docker_environment.lib.data.environment_info import EnvironmentInfo
from exasol_integration_test_docker_environment.lib.data.test_container_content_description import \
    TestContainerContentDescription
from exasol_integration_test_docker_environment.lib.docker.container.utils import remove_docker_container
from exasol_integration_test_docker_environment.lib.docker.volumes.utils import remove_docker_volumes
from exasol_integration_test_docker_environment.lib.docker.networks.utils import remove_docker_networks
from exasol_integration_test_docker_environment.lib.test_environment.spawn_test_environment_with_docker_db import \
    SpawnTestEnvironmentWithDockerDB


def _cleanup(environment_info: EnvironmentInfo) -> None:
    if environment_info.test_container_info is None:
        remove_docker_container([environment_info.database_info.container_info.container_name])
    else:
        remove_docker_container([environment_info.test_container_info.container_name,
                                 environment_info.database_info.container_info.container_name])
    remove_docker_volumes([environment_info.database_info.container_info.volume_name])
    remove_docker_networks([environment_info.network_info.network_name])


@no_cli_function
def spawn_test_environment_with_test_container(
        environment_name: str,
        test_container_content: TestContainerContentDescription,
        database_port_forward: Optional[int] = None,
        bucketfs_port_forward: Optional[int] = None,
        db_mem_size: str = "2 GiB",
        db_disk_size: str = "2 GiB",
        nameserver: Tuple[str, ...] = tuple(),
        docker_runtime: Optional[str] = None,
        docker_db_image_version: str = LATEST_DB_VERSION,
        docker_db_image_name: str = "exasol/docker-db",
        create_certificates: bool = False,
        additional_db_parameter: Tuple[str, ...] = tuple(),
        source_docker_repository_name: str = DEFAULT_DOCKER_REPOSITORY_NAME,
        source_docker_tag_prefix: str = '',
        source_docker_username: Optional[str] = None,
        source_docker_password: Optional[str] = None,
        target_docker_repository_name: str = DEFAULT_DOCKER_REPOSITORY_NAME,
        target_docker_tag_prefix: str = '',
        target_docker_username: Optional[str] = None,
        target_docker_password: Optional[str] = None,
        output_directory: str = DEFAULT_OUTPUT_DIRECTORY,
        temporary_base_directory: str = "/tmp",
        workers: int = 5,
        task_dependencies_dot_file: Optional[str] = None,
        log_level: Optional[str] = None,
        use_job_specific_log_file: bool = False
) \
        -> Tuple[EnvironmentInfo, Callable[[], None]]:
    """
    This function spawns a test environment with a docker-db container and a connected test-container.
    The test-container is reachable by the database for output redirects of UDFs.
    The function returns an environment_info object, describing the environment, and a cleanup-method, which
    can be used to stop the environment.
    raises: TaskRuntimeError if spawning the test environment fails

    """
    parsed_db_mem_size = humanfriendly.parse_size(db_mem_size)
    if parsed_db_mem_size < humanfriendly.parse_size("1 GiB"):
        raise ArgumentConstraintError("db_mem_size", "needs to be at least 1 GiB")
    parsed_db_disk_size = humanfriendly.parse_size(db_disk_size)
    if parsed_db_disk_size < humanfriendly.parse_size("100 MiB"):
        raise ArgumentConstraintError("db_disk_size", "needs to be at least 100 MiB")
    set_build_config(False,
                     tuple(),
                     False,
                     False,
                     output_directory,
                     temporary_base_directory,
                     None,
                     None)
    set_docker_repository_config(source_docker_password, source_docker_repository_name, source_docker_username,
                                 source_docker_tag_prefix, "source")
    set_docker_repository_config(target_docker_password, target_docker_repository_name, target_docker_username,
                                 target_docker_tag_prefix, "target")
    task_creator = lambda: generate_root_task(task_class=SpawnTestEnvironmentWithDockerDB,
                                              environment_name=environment_name,
                                              database_port_forward=str(
                                                  database_port_forward) if database_port_forward is not None else None,
                                              bucketfs_port_forward=str(
                                                  bucketfs_port_forward) if bucketfs_port_forward is not None else None,
                                              mem_size=db_mem_size,
                                              disk_size=db_disk_size,
                                              nameservers=nameserver,
                                              docker_runtime=docker_runtime,
                                              docker_db_image_version=docker_db_image_version,
                                              docker_db_image_name=docker_db_image_name,
                                              db_user="sys",
                                              db_password="exasol",
                                              bucketfs_write_password="write",
                                              no_test_container_cleanup_after_success=True,
                                              no_test_container_cleanup_after_failure=False,
                                              no_database_cleanup_after_success=True,
                                              no_database_cleanup_after_failure=False,
                                              create_certificates=create_certificates,
                                              test_container_content=test_container_content,
                                              additional_db_parameter=additional_db_parameter
                                              )
    environment_info = run_task(task_creator, workers, task_dependencies_dot_file,
                                log_level=log_level,
                                use_job_specific_log_file=use_job_specific_log_file)
    return environment_info, functools.partial(_cleanup, environment_info)
