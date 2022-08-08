import unittest

from exasol_integration_test_docker_environment.lib import api
from exasol_integration_test_docker_environment.testing.api_test_environment import ApiTestEnvironment
from exasol_integration_test_docker_environment.testing.docker_registry import create_local_registry


class APIPushTestContainerTest(unittest.TestCase):

    def setUp(self):
        print(f"SetUp {self.__class__.__name__}")
        self.test_environment = ApiTestEnvironment(self)
        self.test_environment.docker_registry = create_local_registry(self.test_environment.name)
        print("registry:", self.test_environment.docker_registry.request_registry_repositories())

    def tearDown(self):
        self.test_environment.close()

    def test_docker_push(self):
        docker_registry = self.test_environment.docker_registry
        image_info = api.push_test_container(source_docker_repository_name=docker_registry.repository_name,
                                             target_docker_repository_name=docker_registry.repository_name)
        print("repos:", docker_registry.request_registry_repositories())
        images = docker_registry.request_registry_images()
        print("images", images)
        self.assertEqual(len(images["tags"]), 1,
                         f"{images} doesn't have the expected 110 tags, it has {len(images['tags'])}")
        self.assertIn(image_info.get_target_complete_tag(), images["tags"][0])


if __name__ == '__main__':
    unittest.main()
