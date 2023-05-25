import contextlib
import logging
import pytest
from typing import Any, Callable, Dict, Iterator, List, Optional

from exasol_integration_test_docker_environment \
    .testing.api_test_environment import ApiTestEnvironment
from exasol_integration_test_docker_environment \
    .test.get_test_container_content import get_test_container_content

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


@pytest.fixture
def cli_database(cli_isolation) -> Callable[[Optional[str],Optional[List[str]]],SpawnedTestEnvironments]:
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


@pytest.fixture
def api_database(api_isolation: ApiTestEnvironment) -> Callable[[Optional[str],Optional[Dict[str, Any]]],ExaslctDockerTestEnvironment]:
    @contextlib.contextmanager
    def create_context(
            name: Optional[str] = None,
            additional_parameters: Optional[Dict[str, Any]] = None,
    )->ExaslctDockerTestEnvironment:
        name = name if name else api_isolation.name
        spawned = api_isolation.spawn_docker_test_environment(
            name=name,
            additional_parameter=additional_parameters,
        )
        yield spawned
        utils.close_environments(spawned)
    return create_context


@contextlib.contextmanager
def container_named(name):
    with ContextDockerClient() as client:
        matches = [c for c in client.containers.list() if c.name == name]
        yield matches[0] if matches else None


@contextlib.contextmanager
def container_with_names(*names):
    match = lambda value: all(x in value for x in names)
    with ContextDockerClient() as client:
        matches = [c for c in client.containers.list() if match(c.name)]
        yield matches[0] if matches else None