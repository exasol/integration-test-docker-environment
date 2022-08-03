from typing import Tuple, Optional
import humanfriendly

from exasol_integration_test_docker_environment.cli.common import set_build_config, set_docker_repository_config, \
    run_task, generate_root_task
from exasol_integration_test_docker_environment.cli.options.docker_repository_options import DEFAULT_DOCKER_REPOSITORY_NAME
from exasol_integration_test_docker_environment.cli.options.system_options import DEFAULT_OUTPUT_DIRECTORY
from exasol_integration_test_docker_environment.cli.options.test_environment_options import LATEST_DB_VERSION
from exasol_integration_test_docker_environment.lib.api.api_errors import ArgumentConstraintError
from exasol_integration_test_docker_environment.lib.test_environment.spawn_test_environment_with_docker_db import \
    SpawnTestEnvironmentWithDockerDB


def spawn_test_environment(
        environment_name: str,
        database_port_forward: Optional[int] = None,
        bucketfs_port_forward: Optional[int] = None,
        db_mem_size: str = "2 GiB",
        db_disk_size: str = "2 GiB",
        nameserver: Tuple[str,...] = tuple(),
        deactivate_database_setup: bool = False,
        docker_runtime: Optional[str] = None,
        docker_db_image_version: str = LATEST_DB_VERSION,
        docker_db_image_name: str = "exasol/docker-db",
        create_certificates: bool = False,
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
        task_dependencies_dot_file: Optional[str] = None) -> bool:
    """
    This command spawn a test environment with a docker-db container and a connected test-container.
    The test-container is reachable by the database for output redirects of UDFs.
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
                                              is_setup_database_activated=not deactivate_database_setup,
                                              create_certificates=create_certificates
                                              )
    success, task = run_task(task_creator, workers, task_dependencies_dot_file)
    return success
