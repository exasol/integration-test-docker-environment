import pytest

from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing \
   .exaslct_test_environment import ExaslctTestEnvironment

class PyTestEnvironment:
    def __init__(self):
        # print(f"SetUp {cls.__name__}")
        self.environment = ExaslctTestEnvironment(self, "itde", clean_images_at_close=False)
        self.docker_environment_name = self.__class__.__name__
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
