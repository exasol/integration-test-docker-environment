import unittest
from sys import stderr

from exasol_integration_test_docker_environment.lib import api
from exasol_integration_test_docker_environment.testing.api_test_environment import ApiTestEnvironment
from exasol_integration_test_docker_environment.testing.docker_registry import create_local_registry


class APIPushTestContainerTest(unittest.TestCase):

    def setUp(self):
        print(f"SetUp {self.__class__.__name__}", file=stderr)
        self.test_environment = ApiTestEnvironment(self)
        self.docker_registry = create_local_registry(self.test_environment.name)
        self.test_environment.docker_registry_description = self.docker_registry.docker_registry_description
        print("registry:", self.docker_registry.request_registry_repositories(), file=stderr)

    def tearDown(self):
        self.docker_registry.close()

    def test_docker_push(self):
        docker_repository_name = self.docker_registry.docker_registry_description.repository_name
        image_info = api.push_test_container(source_docker_repository_name=docker_repository_name,
                                             target_docker_repository_name=docker_repository_name)
        print("repos:", self.docker_registry.request_registry_repositories(), file=stderr)
        images = self.docker_registry.request_registry_images()
        print("images", images, file=stderr)
        self.assertEqual(len(images["tags"]), 1,
                         f"{images} doesn't have the expected 110 tags, it has {len(images['tags'])}")
        self.assertIn(image_info.get_target_complete_tag(), images["tags"][0])


if __name__ == '__main__':
    unittest.main()
