import click
import humanfriendly

from ..cli import cli
from ..common import set_build_config, run_task, add_options, set_job_id
from ..options.system_options import tempory_base_directory_option, system_options, \
    output_directory_option
from ..options.test_environment_options import docker_db_options
from ...lib.test_environment.spawn_test_environment_with_docker_db import \
    SpawnTestEnvironmentWithDockerDB


@cli.command()
@click.option('--environment-name', type=str, required=True, help="Name of the docker environment. This name gets used as suffix for the container db_container_<name> and test_container_<name>")
@click.option('--database-port-forward', type=int, default=8888, show_default=True,
        help="Host port to which the database port gets forwarded")
@click.option('--bucketfs-port-forward', type=int, default=6666,  show_default=True,
        help="Host port to which the bucketfs port gets forwarded")
@click.option('--db-mem-size', type=str, default="2 GiB", show_default=True,
        help="The main memory used by the database. Format <number> <unit>, e.g. 1 GiB. The minimum size is 1 GB, below that the database will not start.")
@add_options(docker_db_options)
@add_options([output_directory_option])
@add_options([tempory_base_directory_option])
@add_options(system_options)
def spawn_test_environment(
        environment_name: str,
        database_port_forward: int,
        bucketfs_port_forward: int,
        db_mem_size:str,
        docker_db_image_version: str,
        docker_db_image_name: str,
        output_directory: str,
        temporary_base_directory: str,
        workers: int,
        task_dependencies_dot_file: str):
    """
    This command spawn a test environment with a docker-db container and a conected test-container.
    The test-container is reachable by the database for output redirects of udfs.
    """
    humanfriendly_db_mem_size = humanfriendly.parse_size(db_mem_size)
    if humanfriendly_db_mem_size<1000000000: # db_mem_size needs to be larger than 1000 MB
        print("The --db-mem-size needs to be at least 1 GiB.")
        exit(1)
    set_build_config(False,
                     tuple(),
                     False,
                     False,
                     output_directory,
                     temporary_base_directory,
                     None,
                     None)
    task_creator = lambda: SpawnTestEnvironmentWithDockerDB(
        environment_name=environment_name,
        database_port_forward=str(database_port_forward),
        bucketfs_port_forward=str(bucketfs_port_forward),
        mem_size=db_mem_size,
        docker_db_image_version=docker_db_image_version,
        docker_db_image_name=docker_db_image_name,
        db_user="sys",
        db_password="exasol",
        bucketfs_write_password="write",
        no_test_container_cleanup_after_end=True,
        no_database_cleanup_after_end=True
    )
    set_job_id(SpawnTestEnvironmentWithDockerDB.__name__)
    success, task = run_task(task_creator, workers, task_dependencies_dot_file)
    if not success:
        exit(1)
