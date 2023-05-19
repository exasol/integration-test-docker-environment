import logging
import pytest

from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing \
   .exaslct_test_environment import ExaslctTestEnvironment


_logger = logging.getLogger(__name__)


class PyTestEnvironment:
    def __init__(self):
        self.docker_environment_name = self.__class__.__name__
        _logger.info(f"SetUp {self.docker_environment_name}")
        self.environment = ExaslctTestEnvironment(self, "itde", clean_images_at_close=False)
        self.spawned = self.environment.spawn_docker_test_environments(
            name=self.docker_environment_name,
            additional_parameter = ["--docker-access-method", "SSH"],
        )

    def cleanup(self):
        utils.close_environments(self.spawned, self.environment)


@pytest.fixture
def slc_environment():
    environment = PyTestEnvironment()
    yield environment
    environment.cleanup()
