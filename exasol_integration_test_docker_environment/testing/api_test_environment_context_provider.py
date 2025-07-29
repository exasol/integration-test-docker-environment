import contextlib
from collections.abc import (
    Generator,
    Iterator,
)
from typing import (
    Any,
    ContextManager,
    Optional,
    Protocol,
)

from exasol_integration_test_docker_environment.lib.models.data.test_container_content_description import (
    TestContainerContentDescription,
)
from exasol_integration_test_docker_environment.testing import (
    luigi_utils,
    utils,
)
from exasol_integration_test_docker_environment.testing.api_test_environment import (
    ApiTestEnvironment,
)
from exasol_integration_test_docker_environment.testing.exaslct_docker_test_environment import (
    ExaslctDockerTestEnvironment,
)


@contextlib.contextmanager
def build_api_isolation(request) -> Iterator[ApiTestEnvironment]:
    """
    Builds an ApiTestEnvironment instance with a proper name based on the pytest request fixture.
    Cleans up the environment automatically on shutdown.
    """
    testname = utils.normalize_request_name(request.node.name)
    environment = ApiTestEnvironment(test_object=None, name=testname)
    yield environment
    utils.close_environments(environment)
    luigi_utils.clean(environment.docker_repository_name)


class ApiContextProvider(Protocol):
    def __call__(
        self,
        name: Optional[str],
        additional_parameters: Optional[dict[str, Any]] = None,
    ) -> ContextManager[ExaslctDockerTestEnvironment]: ...


def build_api_context_provider(
    test_environment: ApiTestEnvironment,
) -> ApiContextProvider:
    """
    Returns a context provider function which can be used to spawn a Docker DB with custom name and custom additional db parameters.
    Cleans up the docker db automatically on shutdown when context provider closes.
    """

    @contextlib.contextmanager
    def create_context(
        name: Optional[str] = None,
        additional_parameters: Optional[dict[str, Any]] = None,
    ) -> Generator[ExaslctDockerTestEnvironment, None, None]:
        name = name if name else test_environment.name
        spawned = test_environment.spawn_docker_test_environment(
            name=name,
            additional_parameter=additional_parameters,
        )
        yield spawned
        utils.close_environments(spawned)

    return create_context


class ApiContextProviderWithTestContainer(Protocol):
    def __call__(
        self,
        name: Optional[str],
        additional_parameters: Optional[dict[str, Any]] = None,
        test_container_content: Optional[TestContainerContentDescription] = None,
    ) -> ContextManager[ExaslctDockerTestEnvironment]: ...


def build_api_context_provider_with_test_container(
    test_environment: ApiTestEnvironment,
    default_test_container_content: TestContainerContentDescription,
) -> ApiContextProviderWithTestContainer:
    """
    Returns a context provider function which can be used to spawn a Docker DB + Test container
    with custom name, custom additional db parameters and custom test container content.
    Cleans up the docker db + test container automatically on shutdown when context provider closes.
    """

    @contextlib.contextmanager
    def create_context(
        name: Optional[str] = None,
        additional_parameters: Optional[dict[str, Any]] = None,
        test_container_content=default_test_container_content,
    ) -> Generator[ExaslctDockerTestEnvironment, None, None]:
        name = name if name else test_environment.name
        spawned = test_environment.spawn_docker_test_environment_with_test_container(
            name=name,
            additional_parameter=additional_parameters,
            test_container_content=test_container_content,
        )
        yield spawned
        utils.close_environments(spawned)

    return create_context
