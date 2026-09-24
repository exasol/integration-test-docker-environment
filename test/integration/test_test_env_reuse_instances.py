from test.integration._test_env_reuse_common import (
    ReusingTestEnv,
    get_instance_ids,
)


def test_reuse_instances(reusing_test_env: ReusingTestEnv):
    """Reuse the test container, database setup, database, and network."""
    first_task = reusing_test_env.run_spawn_test_env(cleanup=False)
    try:
        old_ids = get_instance_ids(first_task.get_result())
        first_task.cleanup(True)
        second_task = reusing_test_env.run_spawn_test_env(cleanup=True)
        try:
            assert get_instance_ids(second_task.get_result()) == old_ids
        finally:
            second_task.cleanup(False)
    except Exception:
        first_task.cleanup(False)
        raise
