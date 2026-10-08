from pathlib import Path

import pytest

from test.integration.env_reuse import confd_credentials
from test.integration.env_reuse.environment import ReusingTestEnv


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
        confd_credentials.remove_client_executable_permission(
            database_container_info.container_name,
            first_environment.database_info.host,
        )
        with pytest.raises(RuntimeError, match="Error spawning test environment"):
            reusing_test_env.run_spawn_test_env(
                cleanup=True, create_confd_user=True, include_test_container=False
            )
        assert not credentials_file.exists()
    finally:
        first_task.cleanup(False)
