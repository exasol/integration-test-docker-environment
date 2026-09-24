from pathlib import Path
from test.integration._test_env_reuse_common import ReusingTestEnv


def test_reuse_returns_existing_confd_credentials(reusing_test_env: ReusingTestEnv):
    """Reuse a Docker-DB ConfD account without recreating or changing it."""
    first_task = reusing_test_env.run_spawn_test_env(
        cleanup=False, create_confd_user=True, include_test_container=False
    )
    second_task = None
    try:
        first_confd_info = first_task.get_result().database_info.confd_info
        assert first_confd_info is not None
        credentials_file = Path(first_confd_info.credentials_file)
        assert credentials_file.exists()
        credentials = first_confd_info.read_credentials()

        first_task.cleanup(True)
        second_task = reusing_test_env.run_spawn_test_env(
            cleanup=True, create_confd_user=True, include_test_container=False
        )
        second_environment = second_task.get_result()
        second_confd_info = second_environment.database_info.confd_info
        assert second_confd_info is not None
        assert second_environment.database_info.reused
        assert second_confd_info.credentials_file == str(credentials_file)
        assert second_confd_info.read_credentials().password == credentials.password
    finally:
        (second_task or first_task).cleanup(False)
