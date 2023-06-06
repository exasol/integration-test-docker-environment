import contextlib
import logging
import pytest
from typing import Any, Callable, Dict, Iterator, List, NewType, Optional

from exasol_integration_test_docker_environment \
    .testing.api_test_environment import ApiTestEnvironment
from exasol_integration_test_docker_environment \
    .testing.exaslct_docker_test_environment import \
    ExaslctDockerTestEnvironment
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing \
   .exaslct_test_environment import (
       ExaslctTestEnvironment,
       SpawnedTestEnvironments,
   )


@pytest.fixture
def cli_isolation(request) -> Iterator[ExaslctTestEnvironment]:
    testname = request.node.name
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
    testname = request.node.name
    environment = ApiTestEnvironment(test_object=None, name=testname)
    yield environment
    utils.close_environments(environment)


CliContextProvider = NewType(
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
    @contextlib.contextmanager
    def create_context(
            name: Optional[str] = None,
            additional_parameters: Optional[List[str]] = None,
    )->SpawnedTestEnvironments:
        name = name if name else cli_isolation.name
        spawned = cli_isolation.spawn_docker_test_environments(
            name=name,
            additional_parameter=additional_parameters,
        )
        yield spawned
        utils.close_environments(spawned)
    return create_context


ApiContextProvider = NewType(
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
    ) -> ExaslctDockerTestEnvironment:
        name = name if name else api_isolation.name
        spawned = api_isolation.spawn_docker_test_environment(
            name=name,
            additional_parameter=additional_parameters,
        )
        yield spawned
        utils.close_environments(spawned)
    return create_context


def exact_matcher(names):
    return lambda value: all(x == value for x in names)


def superset_matcher(names):
    return lambda value: all(x in value for x in names)


@contextlib.contextmanager
def container_named(*names, matcher=None):
    matcher = matcher if matcher else exact_matcher(names)
    with ContextDockerClient() as client:
        matches = [c for c in client.containers.list() if matcher(c.name)]
        yield matches[0] if matches else None
