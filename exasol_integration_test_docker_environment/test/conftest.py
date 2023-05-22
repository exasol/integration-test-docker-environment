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


@contextlib.contextmanager
def database(itde_test_isolation: ExaslctTestEnvironment,
             name: Optional[str] = None,
             additional_parameters=Optional[List[str]] = None,
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


# class PyTestEnvironment:
#     def __init__(self):
#         self.docker_environment_name = self.__class__.__name__
#         _logger.info(f"SetUp {self.docker_environment_name}")
#         self.environment = ExaslctTestEnvironment(self, "itde", clean_images_at_close=False)
#         self.spawned = self.environment.spawn_docker_test_environments(
#             name=self.docker_environment_name,
#             additional_parameter = ["--db-os-access", "SSH"],
#         )
#
#     def cleanup(self):
#         utils.close_environments(self.spawned, self.environment)


# @pytest.fixture
# def slc_environment():
#     environment = PyTestEnvironment()
#     yield environment
#     environment.cleanup()
