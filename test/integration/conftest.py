import contextlib
import io

import pytest

from typing import Any, Callable, Dict, Iterator, List, NewType, Optional, Generator

from typing_extensions import Never

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from test.integration.helpers import normalize_request_name
from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment \
    .testing.api_test_environment import ApiTestEnvironment
from exasol_integration_test_docker_environment \
    .testing.exaslct_docker_test_environment import \
    ExaslctDockerTestEnvironment
from exasol_integration_test_docker_environment.testing \
    .exaslct_test_environment import (
    ExaslctTestEnvironment,
    SpawnedTestEnvironments,
)


@pytest.fixture
def cli_isolation(request) -> Iterator[ExaslctTestEnvironment]:
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
def api_isolation(request) -> Iterator[ApiTestEnvironment]:
    testname = normalize_request_name(request.node.name)
    environment = ApiTestEnvironment(test_object=None, name=testname)
    yield environment
    utils.close_environments(environment)


CliContextProvider = NewType( # type: ignore
    "CliContextProvider", Callable[
        [Optional[str], Optional[List[str]]],
        SpawnedTestEnvironments
    ],
)


@pytest.fixture
def cli_database(cli_isolation) -> CliContextProvider:
    """
    Returns a method that test case implementations can use to create a
    context with a database.

    The test case optionally can pass a name and additional parameters for
    spawning the database:

    def test_case(database):
        with database(additional_parameters = ["--option"]):
            ...
    """

    @contextlib.contextmanager # type: ignore
    def create_context( # type: ignore
            name: Optional[str] = None, # type: ignore
            additional_parameters: Optional[List[str]] = None,
    ) -> SpawnedTestEnvironments:
        name = name if name else cli_isolation.name
        spawned = cli_isolation.spawn_docker_test_environments(
            name=name,
            additional_parameter=additional_parameters,
        )
        yield spawned
        utils.close_environments(spawned)

    return create_context # type: ignore


ApiContextProvider = NewType( # type: ignore
    "ApiContextProvider",
    Callable[
        [Optional[str], Optional[Dict[str, Any]]],
        ExaslctDockerTestEnvironment
    ],
)


@pytest.fixture
def api_database(api_isolation: ApiTestEnvironment) -> ApiContextProvider:
    @contextlib.contextmanager
    def create_context(
            name: Optional[str] = None,
            additional_parameters: Optional[Dict[str, Any]] = None,
    ) -> Generator[ExaslctDockerTestEnvironment, None, None]:
        name = name if name else api_isolation.name
        spawned = api_isolation.spawn_docker_test_environment(
            name=name,
            additional_parameter=additional_parameters,
        )
        yield spawned
        utils.close_environments(spawned)

    return create_context # type: ignore

@pytest.fixture
def fabric_stdin(monkeypatch):
    """
    Mock stdin to avoid ThreadException when reading from stdin while
    stdout is captured by pytest: OSError: pytest: reading from stdin while
    output is captured!  Consider using ``-s``.
    See https://github.com/fabric/fabric/issues/2005
    """
    monkeypatch.setattr('sys.stdin', io.StringIO(''))
