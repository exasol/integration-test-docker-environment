from typing import Tuple, Optional

from exasol_integration_test_docker_environment.cli.cli import cli
from exasol_integration_test_docker_environment.cli.common import add_options
from exasol_integration_test_docker_environment.cli.options.build_options import build_options
from exasol_integration_test_docker_environment.cli.options.docker_repository_options import docker_repository_options
from exasol_integration_test_docker_environment.cli.options.push_options import push_options
from exasol_integration_test_docker_environment.cli.options.system_options import system_options
from exasol_integration_test_docker_environment.lib import api


@cli.command()
@add_options(push_options)
@add_options(build_options)
@add_options(docker_repository_options)
@add_options(system_options)
def push_test_container(
        force_push: bool,
        push_all: bool,
        force_rebuild: bool,
        force_rebuild_from: Tuple[str, ...],
        force_pull: bool,
        output_directory: str,
        temporary_base_directory: str,
        log_build_context_content: bool,
        cache_directory: Optional[str],
        build_name: Optional[str],
        source_docker_repository_name: str,
        source_docker_tag_prefix: str,
        source_docker_username: Optional[str],
        source_docker_password: Optional[str],
        target_docker_repository_name: str,
        target_docker_tag_prefix: str,
        target_docker_username: Optional[str],
        target_docker_password: Optional[str],
        workers: int,
        task_dependencies_dot_file: Optional[str]):
    """
    This command pushs all stages of the test container for the test environment.
    If the stages do not exists locally, the system will build or pull them before the push.
    """
    success = api.push_test_container(force_push,
                                      push_all,
                                      force_rebuild,
                                      force_rebuild_from,
                                      force_pull,
                                      output_directory,
                                      temporary_base_directory,
                                      log_build_context_content,
                                      cache_directory,
                                      build_name,
                                      source_docker_repository_name,
                                      source_docker_tag_prefix,
                                      source_docker_username,
                                      source_docker_password,
                                      target_docker_repository_name,
                                      target_docker_tag_prefix,
                                      target_docker_username,
                                      target_docker_password,
                                      workers,
                                      task_dependencies_dot_file)
    if not success:
        exit(1)
