import contextlib
import io
from test.integration.helpers import normalize_request_name
from typing import (
    Any,
    Callable,
    ContextManager,
    Dict,
    Generator,
    Iterator,
    List,
    NewType,
    Optional,
)

import pytest

from exasol_integration_test_docker_environment.testing import utils, luigi_utils
from exasol_integration_test_docker_environment.testing.api_test_environment import (
    ApiTestEnvironment,
)
from exasol_integration_test_docker_environment.testing.exaslct_docker_test_environment import (
    ExaslctDockerTestEnvironment,
)
from exasol_integration_test_docker_environment.testing.exaslct_test_environment import (
    ExaslctTestEnvironment,
    SpawnedTestEnvironments,
)

@contextlib.contextmanager
def _build_cli_isolation(request) -> Iterator[ExaslctTestEnvironment]:
    testname = normalize_request_name(request.node.name)
    environment = ExaslctTestEnvironment(
        test_object=None,
        executable="itde",
        clean_images_at_close=True,
        name=testname,
    )
    yield environment
    utils.close_environments(environment)

@pytest.fixture
def cli_isolation(request) -> Iterator[ExaslctTestEnvironment]:
    with _build_cli_isolation(request) as environment:
        yield environment

@pytest.fixture(scope="module")
def cli_isolation_module(request) -> Iterator[ExaslctTestEnvironment]:
    with _build_cli_isolation(request) as environment:
        yield environment

@contextlib.contextmanager
def _build_api_isolation(request) -> Iterator[ApiTestEnvironment]:
    testname = normalize_request_name(request.node.name)
    environment = ApiTestEnvironment(test_object=None, name=testname)
    yield environment
    utils.close_environments(environment)
    luigi_utils.clean(environment.docker_repository_name)


@pytest.fixture
def api_isolation(request) -> Iterator[ApiTestEnvironment]:
    with _build_api_isolation(request) as environment:
        yield environment

@pytest.fixture(scope="module")
def api_isolation_module(request) -> Iterator[ApiTestEnvironment]:
    with _build_api_isolation(request) as environment:
        yield environment


CliContextProvider = NewType(  # type: ignore
    "CliContextProvider",
    Callable[[Optional[str], Optional[List[str]]], Iterator[SpawnedTestEnvironments]],
)

def _build_cli_context_provider(test_environment: ExaslctTestEnvironment) -> CliContextProvider:
    @contextlib.contextmanager
    def create_context(
            name: Optional[str] = None,
            additional_parameters: Optional[List[str]] = None,
    ) -> Iterator[SpawnedTestEnvironments]:
        name = name if name else test_environment.name
        spawned = test_environment.spawn_docker_test_environments(
            name=name,
            additional_parameter=additional_parameters,
        )
        yield spawned
        utils.close_environments(spawned)
    return create_context

@pytest.fixture
def cli_database(
    cli_isolation,
) -> CliContextProvider:
    """
    Returns a method that test case implementations can use to create a
    context with a database.

    The test case optionally can pass a name and additional parameters for
    spawning the database:

    def test_case(database):
        with database(additional_parameters = ["--option"]):
            ...
    """
    return _build_cli_context_provider(cli_isolation)


@pytest.fixture(scope="module")
def cli_database_module(
    cli_isolation_module,
) -> CliContextProvider:
    """
    Returns a method that test case implementations can use to create a
    context with a database.

    The test case optionally can pass a name and additional parameters for
    spawning the database:

    def test_case(database):
        with database(additional_parameters = ["--option"]):
            ...
    """
    return _build_cli_context_provider(cli_isolation_module)

ApiContextProvider = NewType(  # type: ignore
    "ApiContextProvider",
    Callable[[Optional[str], Optional[Dict[str, Any]]], ExaslctDockerTestEnvironment],
)


def _build_api_context_provider(test_environment: ApiTestEnvironment) -> ApiContextProvider:
    @contextlib.contextmanager
    def create_context(
        name: Optional[str] = None,
        additional_parameters: Optional[Dict[str, Any]] = None,
    ) -> Generator[ExaslctDockerTestEnvironment, None, None]:
        name = name if name else test_environment.name
        spawned = test_environment.spawn_docker_test_environment(
            name=name,
            additional_parameter=additional_parameters,
        )
        yield spawned
        utils.close_environments(spawned)

    return create_context  # type: ignore

@pytest.fixture
def api_database(api_isolation: ApiTestEnvironment) -> ApiContextProvider:
    return _build_api_context_provider(api_isolation)

@pytest.fixture(scope="module")
def api_database_module(api_isolation_module: ApiTestEnvironment) -> ApiContextProvider:
    return _build_api_context_provider(api_isolation_module)


@pytest.fixture
def fabric_stdin(monkeypatch):
    """
    Mock stdin to avoid ThreadException when reading from stdin while
    stdout is captured by pytest: OSError: pytest: reading from stdin while
    output is captured!  Consider using ``-s``.
    See https://github.com/fabric/fabric/issues/2005
    """
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
