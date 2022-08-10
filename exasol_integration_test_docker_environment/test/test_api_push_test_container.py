import unittest
from sys import stderr

from exasol_integration_test_docker_environment.lib import api
from exasol_integration_test_docker_environment.testing.api_test_environment import ApiTestEnvironment
from exasol_integration_test_docker_environment.testing.docker_registry import LocalDockerRegistryContextManager


class APIPushTestContainerTest(unittest.TestCase):

    def setUp(self):
        print(f"SetUp {self.__class__.__name__}", file=stderr)
        self.test_environment = ApiTestEnvironment(self)

    def tearDown(self):
        self.test_environment.close()

    def test_docker_push(self):
        with LocalDockerRegistryContextManager(self.test_environment.name) as docker_registry:
            print("registry:", docker_registry.repositories, file=stderr)
            docker_repository_name = docker_registry.name
            image_info = api.push_test_container(source_docker_repository_name=docker_repository_name,
                                                 target_docker_repository_name=docker_repository_name)
            print("repos:", docker_registry.repositories, file=stderr)
            images = docker_registry.images
            print("images", images, file=stderr)
            self.assertEqual(len(images["tags"]), 1,
                             f"{images} doesn't have the expected 1 tags, it has {len(images['tags'])}")
            self.assertIn(image_info.get_target_complete_tag(), images["tags"][0])


if __name__ == '__main__':
    unittest.main()
