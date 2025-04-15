from test.integration.docker_runtime.common import (
    assert_container_runtime,
    default_docker_runtime,
)


def test_test_container_runtime(
    api_default_database_with_test_conainer_module, default_docker_runtime
):
    env = api_default_database_with_test_conainer_module.environment_info
    container_name = env.test_container_info.container_name
    assert_container_runtime(container_name, default_docker_runtime)


def test_database_container_runtime(
    api_default_database_with_test_conainer_module, default_docker_runtime
):
    env = api_default_database_with_test_conainer_module.environment_info
    container_name = env.database_info.container_info.container_name
    assert_container_runtime(container_name, default_docker_runtime)
