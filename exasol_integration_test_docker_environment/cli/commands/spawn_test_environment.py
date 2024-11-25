from typing import (
    Optional,
    Tuple,
)

import click

from exasol_integration_test_docker_environment.cli.cli import cli
from exasol_integration_test_docker_environment.cli.options.docker_repository_options import (
    docker_repository_options,
)
from exasol_integration_test_docker_environment.cli.options.system_options import (
    luigi_logging_options,
    output_directory_option,
    system_options,
    tempory_base_directory_option,
)
from exasol_integration_test_docker_environment.cli.options.test_environment_options import (
    docker_db_options,
)
from exasol_integration_test_docker_environment.cli.termination_handler import (
    TerminationHandler,
)
from exasol_integration_test_docker_environment.lib import api
from exasol_integration_test_docker_environment.lib.api.api_errors import (
    ArgumentConstraintError,
)
from exasol_integration_test_docker_environment.lib.api.common import add_options


@cli.command()
@click.option(
    "--environment-name",
    type=str,
    required=True,
    help="Name of the docker environment. This name gets used as suffix for the container db_container_<name> and test_container_<name>",
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
    "--ssh-port-forward",
    type=int,
    default=None,
    show_default=True,
    help="Host port to which the SSH port gets forwarded. If not specified then ITDE selects a random free port.",
)
@click.option(
    "--db-mem-size",
    type=str,
    default="2 GiB",
    show_default=True,
    help="The main memory used by the database. Format <number> <unit>, e.g. 1 GiB. The minimum size is 1 GB, below that the database will not start.",
)
@click.option(
    "--db-disk-size",
    type=str,
    default="2 GiB",
    show_default=True,
    help="The disk size available for the database. Format <number> <unit>, e.g. 1 GiB. The minimum size is 100 MiB. However, the setup creates volume files with at least 2 GB larger size, because the database needs at least so much more disk.",
)
@click.option(
    "--nameserver",
    type=str,
    default=[],
    multiple=True,
    help="Add a nameserver to the list of DNS nameservers which the docker-db should use for resolving domain names. You can repeat this option to add further nameservers.",
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
@add_options(luigi_logging_options)
def spawn_test_environment(
    environment_name: str,
    database_port_forward: Optional[int],
    bucketfs_port_forward: Optional[int],
    ssh_port_forward: Optional[int],
    db_mem_size: str,
    db_disk_size: str,
    nameserver: Tuple[str, ...],
    docker_runtime: Optional[str],
    docker_db_image_version: str,
    docker_db_image_name: str,
    db_os_access: Optional[str],
    create_certificates: bool,
    additional_db_parameter: Tuple[str, ...],
    source_docker_repository_name: str,
    source_docker_tag_prefix: str,
    source_docker_username: Optional[str],
    source_docker_password: Optional[str],
    target_docker_repository_name: str,
    target_docker_tag_prefix: str,
    target_docker_username: Optional[str],
    target_docker_password: Optional[str],
    output_directory: str,
    temporary_base_directory: str,
    workers: int,
    task_dependencies_dot_file: Optional[str],
    log_level: Optional[str],
    use_job_specific_log_file: bool,
):
    """
    This command spawns a test environment with a docker-db container and a connected test-container.
    The test-container is reachable by the database for output redirects of UDFs.
    """
    with TerminationHandler():
        try:
            api.spawn_test_environment(
                environment_name,
                database_port_forward,
                bucketfs_port_forward,
                ssh_port_forward,
                db_mem_size,
                db_disk_size,
                nameserver,
                docker_runtime,
                docker_db_image_version,
                docker_db_image_name,
                db_os_access,
                create_certificates,
                additional_db_parameter,
                source_docker_repository_name,
                source_docker_tag_prefix,
                source_docker_username,
                source_docker_password,
                target_docker_repository_name,
                target_docker_tag_prefix,
                target_docker_username,
                target_docker_password,
                output_directory,
                temporary_base_directory,
                workers,
                task_dependencies_dot_file,
                log_level=log_level,
                use_job_specific_log_file=use_job_specific_log_file,
            )
        except ArgumentConstraintError as e:
            handle_wrong_argument_error(*e.args)


def handle_wrong_argument_error(argument_name, message):
    formatted = f"--{argument_name}".replace("_", "-")
    print(f"{formatted}: {message}")
    ctx = click.get_current_context()
    click.echo(ctx.get_help())
    exit(1)
