import unittest
from sys import stderr

from exasol_integration_test_docker_environment.lib import api
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.docker.images.image_info import (
    ImageState,
)
from exasol_integration_test_docker_environment.test.get_test_container_content import (
    MOCK_TEST_CONTAINER_PATH,
    get_test_container_content,
)
from exasol_integration_test_docker_environment.testing import luigi_utils
from exasol_integration_test_docker_environment.testing.api_test_environment import (
    ApiTestEnvironment,
)

TEST_CONTAINER_CONTENT = get_test_container_content(MOCK_TEST_CONTAINER_PATH)


class APIBuildTestContainerTest(unittest.TestCase):

    def setUp(self):
        print(f"SetUp {self.__class__.__name__}", file=stderr)
        self.test_environment = ApiTestEnvironment(self)

    def tearDown(self):
        luigi_utils.clean(self.test_environment.docker_repository_name)
        self.test_environment.close()

    def test_build_test_container(self):
        docker_repository_name = self.test_environment.docker_repository_name
        image_info = api.build_test_container(
            target_docker_repository_name=docker_repository_name,
            test_container_content=TEST_CONTAINER_CONTENT,
        )
        with ContextDockerClient() as docker_client:
            image = docker_client.images.get(image_info.get_target_complete_name())
            self.assertEqual(len(image.tags), 1)
            self.assertEqual(image.tags[0], image_info.get_target_complete_name())
            self.assertEqual(image_info.image_state, ImageState.WAS_BUILD.name)

    def test_build_test_container_use_cached(self):
        docker_repository_name = self.test_environment.docker_repository_name
        image_info1 = api.build_test_container(
            target_docker_repository_name=docker_repository_name,
            test_container_content=TEST_CONTAINER_CONTENT,
        )
        self.assertEqual(image_info1.image_state, ImageState.WAS_BUILD.name)
        image_info2 = api.build_test_container(
            target_docker_repository_name=docker_repository_name,
            test_container_content=TEST_CONTAINER_CONTENT,
        )
        self.assertEqual(image_info2.image_state, ImageState.USED_LOCAL.name)

    def test_build_test_container_force_rebuild(self):
        docker_repository_name = self.test_environment.docker_repository_name
        image_info1 = api.build_test_container(
            target_docker_repository_name=docker_repository_name,
            test_container_content=TEST_CONTAINER_CONTENT,
        )
        self.assertEqual(image_info1.image_state, ImageState.WAS_BUILD.name)
        image_info2 = api.build_test_container(
            target_docker_repository_name=docker_repository_name,
            test_container_content=TEST_CONTAINER_CONTENT,
            force_rebuild=True,
        )
        self.assertEqual(image_info2.image_state, ImageState.WAS_BUILD.name)


if __name__ == "__main__":
    unittest.main()
