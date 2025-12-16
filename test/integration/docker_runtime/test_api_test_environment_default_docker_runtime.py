# `default_docker_runtime` is a pytest fixture, which is not in a location
# that the built-in discovery checks (i.e. conftest.py or registered in a conftest.py
# as a pytest_plugin). This means that for now it needs to be imported for these tests
# to work, but unfortunately, some auto-formatting tools may want to remove it, as they
# interpret as standard Python, meaning that its usage is interpreted as only a
# parameter, not a fixture. Thus, we needed to add # noqa: F401.
from test.integration.docker_runtime.common import default_docker_runtime  # noqa: F401
from test.integration.docker_runtime.common import assert_container_runtime


def test_test_container_runtime(
    api_default_env_with_test_container, default_docker_runtime
):
    env = api_default_env_with_test_container.environment_info
    container_name = env.test_container_info.container_name
    assert_container_runtime(container_name, default_docker_runtime)


def test_database_container_runtime(
    api_default_env_with_test_container, default_docker_runtime
):
    env = api_default_env_with_test_container.environment_info
    container_name = env.database_info.container_info.container_name
    assert_container_runtime(container_name, default_docker_runtime)
