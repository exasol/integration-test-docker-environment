from test.integration.env_reuse import confd_credentials
from test.integration.env_reuse.environment import ReusingTestEnv


def test_reuse_returns_existing_confd_credentials(reusing_test_env: ReusingTestEnv):
    """Reuse a Docker-DB ConfD account without recreating or changing it."""
    first_task, credentials_file, first_password = (
        confd_credentials.create_reusable_environment(reusing_test_env)
    )
    second_task = None
    try:
        second_task, second_password = confd_credentials.reuse_environment(
            reusing_test_env, credentials_file
        )

        assert second_password == first_password
    finally:
        (second_task or first_task).cleanup(False)
