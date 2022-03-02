from typing import List

import click
import humanfriendly

from exasol_integration_test_docker_environment.cli import PortMappingType
from exasol_integration_test_docker_environment.cli.cli import cli
from exasol_integration_test_docker_environment.cli.common import (
    add_options,
    generate_root_task,
    run_task,
    set_build_config,
    set_docker_repository_config,
)
from exasol_integration_test_docker_environment.cli.options.docker_repository_options import (
    docker_repository_options,
)
from exasol_integration_test_docker_environment.cli.options.system_options import (
    output_directory_option,
    system_options,
    tempory_base_directory_option,
)
from exasol_integration_test_docker_environment.cli.options.test_environment_options import (
    docker_db_options,
)
from exasol_integration_test_docker_environment.lib.test_environment.spawn_test_environment_with_docker_db import (
    SpawnTestEnvironmentWithDockerDB,
)


@cli.command()
@click.option(
    "--environment-name",
    type=str,
    required=True,
    help=" ".join(
        (
                "Name of the docker environment.",
                "This name gets used as suffix for the container",
                "db_container_<name> and test_container_<name>",
        )
    ),
)
@click.option(
    "--database-port-forward",
    type=int,
    default=None,
    show_default=True,
    help="Host port to which the database port gets forwarded",
)
@click.option(
    "--bucketfs-port-forward",
    type=int,
    default=None,
    show_default=True,
    help="Host port to which the BucketFS port gets forwarded",
)
@click.option(
    "-p",
    "--port-mapping",
    type=PortMappingType(),
    required=False,
    multiple=True,
    help=" ".join([
        "Maps the specified container ports to ports of the host machine.",
        "The expected format is \"<HOST_PORT>:<CONTAINER_PORT>\".",
        "This option can be specified multiple times.",
    ])
)
@click.option(
    "--db-mem-size",
    type=str,
    default="2 GiB",
    show_default=True,
    help=" ".join(
        (
                "The main memory used by the database.",
                "Format <number> <unit>, e.g. 1 GiB.",
                "The minimum size is 1 GB, below that the database will not start.",
        )
    ),
)
@click.option(
    "--db-disk-size",
    type=str,
    default="2 GiB",
    show_default=True,
    help=" ".join(
        (
                "The disk size available for the database.",
                "Format <number> <unit>, e.g. 1 GiB. The minimum size is 100 MiB. However,",
                "the setup creates volume files with at least 2 GB larger size,",
                "because the database needs at least so much more disk.",
        )
    ),
)
@click.option(
    "--nameserver",
    type=str,
    default=[],
    multiple=True,
    help=" ".join(
        (
                "Add a nameserver to the list of DNS nameservers",
                "which the docker-db should use for resolving domain names.",
                "You can repeat this option to add further nameservers.",
        )
    ),
)
@click.option(
    "--deactivate-database-setup/--no-deactivate-database-setup",
    type=bool,
    default=False,
    show_default=True,
    help=" ".join(
        (
                "Deactivates the setup of the spawned database,",
                "this means no data get populated and no JDBC drivers get uploaded.",
                "This can be used either to save time or as a workaround for MacOSX",
                "where the test_container seems not to be able to access the tests directory",
        )
    ),
)
@click.option(
    "--docker-runtime",
    type=str,
    default=None,
    show_default=True,
    help="The docker runtime used to start all containers",
)
@add_options(docker_db_options)
@add_options(docker_repository_options)
@add_options([output_directory_option])
@add_options([tempory_base_directory_option])
@add_options(system_options)
def spawn_test_environment(
        environment_name: str,
        database_port_forward: int,
        bucketfs_port_forward: int,
        port_mapping: [PortMappingType()],
        db_mem_size: str,
        db_disk_size: str,
        nameserver: List[str],
        deactivate_database_setup: bool,
        docker_runtime: str,
        docker_db_image_version: str,
        docker_db_image_name: str,
        source_docker_repository_name: str,
        source_docker_tag_prefix: str,
        source_docker_username: str,
        source_docker_password: str,
        target_docker_repository_name: str,
        target_docker_tag_prefix: str,
        target_docker_username: str,
        target_docker_password: str,
        output_directory: str,
        temporary_base_directory: str,
        workers: int,
        task_dependencies_dot_file: str,
        create_certificates: bool,
):
    """
    This command spawn a test environment with a docker-db container and a connected test-container.
    The test-container is reachable by the database for output redirects of UDFs.
    """
    parsed_db_mem_size = humanfriendly.parse_size(db_mem_size)
    if parsed_db_mem_size < humanfriendly.parse_size("1 GiB"):
        print("The --db-mem-size needs to be at least 1 GiB.")
        exit(1)
    parsed_db_disk_size = humanfriendly.parse_size(db_disk_size)
    if parsed_db_disk_size < humanfriendly.parse_size("100 MiB"):
        print("The --db-disk-size needs to be at least 100 MiB.")
        exit(1)
    set_build_config(
        False,
        tuple(),
        False,
        False,
        output_directory,
        temporary_base_directory,
        None,
        None,
    )
    set_docker_repository_config(
        source_docker_password,
        source_docker_repository_name,
        source_docker_username,
        source_docker_tag_prefix,
        "source",
    )
    set_docker_repository_config(
        target_docker_password,
        target_docker_repository_name,
        target_docker_username,
        target_docker_tag_prefix,
        "target",
    )
    port_mapping.append()
    task_creator = lambda: generate_root_task(
        task_class=SpawnTestEnvironmentWithDockerDB,
        environment_name=environment_name,  
        database_port_forward=str(database_port_forward)
        if database_port_forward is not None
        else None,
        bucketfs_port_forward=str(bucketfs_port_forward)
        if bucketfs_port_forward is not None
        else None,
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
        create_certificates=create_certificates,
    )
    success, task = run_task(task_creator, workers, task_dependencies_dot_file)
    if not success:
        exit(1)
