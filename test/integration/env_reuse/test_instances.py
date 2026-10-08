from test.integration.env_reuse import environment


def test_reuse_instances(reusing_test_env: environment.ReusingTestEnv):
    """Reuse the test container, database setup, database, and network."""
    first_task = reusing_test_env.run_spawn_test_env(cleanup=False)
    try:
        old_ids = environment.get_instance_ids(first_task.get_result())
        first_task.cleanup(True)
        second_task = reusing_test_env.run_spawn_test_env(cleanup=True)
        try:
            assert environment.get_instance_ids(second_task.get_result()) == old_ids
        finally:
            second_task.cleanup(False)
    except Exception:
        first_task.cleanup(False)
        raise
