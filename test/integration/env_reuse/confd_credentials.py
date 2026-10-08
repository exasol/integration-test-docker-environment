from pathlib import Path
from test.integration.env_reuse.environment import ReusingTestEnv

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.test_environment.spawn_test_environment import (
    SpawnTestEnvironment,
)


def create_reusable_environment(
    reusable_environment: ReusingTestEnv,
) -> tuple[SpawnTestEnvironment, Path, str]:
    """Create and preserve an environment with local ConfD credentials."""
    first_task = reusable_environment.run_spawn_test_env(
        cleanup=False, create_confd_user=True, include_test_container=False
    )
    first_confd_info = first_task.get_result().database_info.confd_info
    assert first_confd_info is not None
    credentials_file = Path(first_confd_info.credentials_file)
    assert credentials_file.exists()
    first_password = first_confd_info.read_credentials().password
    first_task.cleanup(True)
    return first_task, credentials_file, first_password


def reuse_environment(
    reusable_environment: ReusingTestEnv, credentials_file: Path
) -> tuple[SpawnTestEnvironment, str]:
    """Reuse the preserved environment and return its ConfD password."""
    second_task = reusable_environment.run_spawn_test_env(
        cleanup=True, create_confd_user=True, include_test_container=False
    )
    second_environment = second_task.get_result()
    second_confd_info = second_environment.database_info.confd_info
    assert second_confd_info is not None
    assert second_environment.database_info.reused
    assert second_confd_info.credentials_file == str(credentials_file)
    assert credentials_file.exists()
    return second_task, second_confd_info.read_credentials().password


def remove_client_executable_permission(
    container_name: str, database_host: str
) -> None:
    """Make ConfD unavailable by removing execute permissions from its client."""
    with ContextDockerClient() as docker_client:
        database_container = docker_client.containers.get(container_name)
        exit_code, _ = database_container.exec_run(
            [
                "/bin/sh",
                "-c",
                'confd_client_path="$(command -v confd_client)" || exit 1; '
                'chmod a-x "$confd_client_path"',
            ],
            environment={
                "CONFD_HOST": database_host,
                "HOSTNAME": "localhost",
            },
        )
    assert exit_code == 0
