from test.integration.docker_runtime.common import assert_container_runtime, default_docker_runtime

def test_test_container_runtime(api_default_database_with_test_conainer_module, default_docker_runtime):
    environment_info = api_default_database_with_test_conainer_module.environment_info
    test_container_name = environment_info.test_container_info.container_name
    assert_container_runtime(test_container_name, default_docker_runtime)

def test_database_container_runtime(api_default_database_with_test_conainer_module, default_docker_runtime):
    environment_info = api_default_database_with_test_conainer_module.environment_info
    database_container_name = (
        environment_info.database_info.container_info.container_name
    )
    assert_container_runtime(database_container_name, default_docker_runtime
    )

