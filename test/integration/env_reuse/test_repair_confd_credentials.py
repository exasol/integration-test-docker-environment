from test.integration.env_reuse import confd_credentials
from test.integration.env_reuse.environment import ReusingTestEnv


def test_reuse_repairs_missing_confd_credentials(reusing_test_env: ReusingTestEnv):
    """Reuse repairs a deleted local ConfD credentials file and rotates its secret."""
    first_task, credentials_file, first_password = (
        confd_credentials.create_reusable_environment(reusing_test_env)
    )
    second_task = None
    try:
        credentials_file.unlink()
        second_task, second_password = confd_credentials.reuse_environment(
            reusing_test_env, credentials_file
        )

        assert second_password != first_password
    finally:
        (second_task or first_task).cleanup(False)
