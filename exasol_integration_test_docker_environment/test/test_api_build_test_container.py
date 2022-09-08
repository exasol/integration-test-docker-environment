import unittest
from sys import stderr

from exasol_integration_test_docker_environment.lib import api
from exasol_integration_test_docker_environment.lib.api.common import generate_root_task
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.test.get_test_container_content import get_test_container_content
from exasol_integration_test_docker_environment.testing import luigi_utils
from exasol_integration_test_docker_environment.testing.api_test_environment import ApiTestEnvironment


class APIBuildTestContainerTest(unittest.TestCase):

    def setUp(self):
        print(f"SetUp {self.__class__.__name__}", file=stderr)
        self.test_environment = ApiTestEnvironment(self)

    def tearDown(self):
        luigi_utils.clean(self.test_environment.docker_repository_name)
        self.test_environment.close()

    def test_build_test_container(self):
        docker_repository_name = self.test_environment.docker_repository_name
        image_info = api.build_test_container(target_docker_repository_name=docker_repository_name,
                                              test_container_content=get_test_container_content())
        with ContextDockerClient() as docker_client:
            image = docker_client.images.get(image_info.get_target_complete_name())
            assert len(image.tags) == 1
            assert image.tags[0] == image_info.get_target_complete_name()


if __name__ == '__main__':
    unittest.main()
