from exasol_integration_test_docker_environment.lib.models import api_errors
from exasol_integration_test_docker_environment.test.get_test_container_content import (
    get_test_container_content,
)
from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing.api_test_environment import (
    ApiTestEnvironment,
)


def test_docker_environment_not_available(api_isolation_module: ApiTestEnvironment):
    exception_thrown = False
    spawn_docker_test_environments_successful = False
    try:
        additional_parameters = {
            "docker_runtime": "AAAABBBBCCCC_INVALID_RUNTIME_111122223333",
        }
        environment = (
            api_isolation_module.spawn_docker_test_environment_with_test_container(
                name=api_isolation_module.name,
                test_container_content=get_test_container_content(),
                additional_parameter=additional_parameters,
            )
        )
        spawn_docker_test_environments_successful = True
        utils.close_environments(environment)
    except api_errors.TaskRuntimeError:
        exception_thrown = True
    assert not spawn_docker_test_environments_successful
    assert exception_thrown
