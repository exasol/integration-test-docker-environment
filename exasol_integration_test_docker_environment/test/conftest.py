import contextlib
import logging
import pytest
from typing import Callable, Iterator, List, Optional

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
    try:
        yield environment
    finally:
        utils.close_environments(environment)


@pytest.fixture
def database(cli_isolation) -> Callable:
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
    ):
        name = name if name else cli_isolation.name
        spawned = cli_isolation.spawn_docker_test_environments(
            name=name,
            additional_parameter=additional_parameters,
        )
        try:
            yield spawned
        finally:
            utils.close_environments(spawned)
    return create_context
