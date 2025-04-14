from test.integration.docker_runtime.common import (
    assert_container_runtime,
    default_docker_runtime,
)

import pytest

from exasol_integration_test_docker_environment.test.get_test_container_content import (
    get_test_container_content,
)
from exasol_integration_test_docker_environment.testing.api_test_environment import (
    ApiTestEnvironment,
)
from exasol_integration_test_docker_environment.testing.api_test_environment_context_provider import (
    build_api_context_provider_with_test_container,
)


@pytest.fixture(scope="module")
def environment_with_specific_docker_runtime(
    api_isolation_module: ApiTestEnvironment, default_docker_runtime
):
    """
    Start the test environment with a specific docker runtime.
    See the user guide for details.
    """
    api_context_provider = build_api_context_provider_with_test_container(
        api_isolation_module, get_test_container_content()
    )
    additional_parameters = {
        "docker_runtime": default_docker_runtime,
    }
    with api_context_provider(
        name=None, additional_parameters=additional_parameters
    ) as db:
        yield db


def test_test_container_runtime(
    environment_with_specific_docker_runtime, default_docker_runtime
):
    env = environment_with_specific_docker_runtime.environment_info
    container_name = env.test_container_info.container_name
    assert_container_runtime(container_name, default_docker_runtime)


def test_database_container_runtime(
    environment_with_specific_docker_runtime, default_docker_runtime
):
    env = environment_with_specific_docker_runtime.environment_info
    container_name = env.database_info.container_info.container_name
    assert_container_runtime(container_name, default_docker_runtime)
