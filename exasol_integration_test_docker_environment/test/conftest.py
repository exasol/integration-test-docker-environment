import logging
import pytest
from typing import Iterator, List, Optional

from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing \
   .exaslct_test_environment import ExaslctTestEnvironment
from exasol_integration_test_docker_environment.testing \
   .exaslct_test_environment import SpawnedTestEnvironments


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
