import contextlib
import logging
import pytest
from typing import Iterator, List, Optional

from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing \
   .exaslct_test_environment import (
       ExaslctTestEnvironment,
       SpawnedTestEnvironments,
   )


@pytest.fixture
def itde_cli_test_isolation(request) -> Iterator[ExaslctTestEnvironment]:
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


@contextlib.contextmanager
def database(itde_test_isolation: ExaslctTestEnvironment,
             name: Optional[str] = None,
             additional_parameters: Optional[List[str]] = None
             ) -> Iterator[SpawnedTestEnvironments]:
    name = name if name else itde_test_isolation.name
    spawned = itde_test_isolation.spawn_docker_test_environments(
        name=name,
        additional_parameter=additional_parameters,
    )
    try:
        yield spawned
    finally:
        utils.close_environments(spawned)
