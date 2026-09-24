from pathlib import Path
from test.integration._test_env_reuse_common import ReusingTestEnv

import pytest

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient


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
