import unittest

from exasol_integration_test_docker_environment.lib import api
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient


class DockerAPIBuildTestContainerTest(unittest.TestCase):

    def test_build_test_container(self):
        image_info = api.build_test_container()
        with ContextDockerClient() as docker_client:
            image = docker_client.images.get(image_info.get_target_complete_name())
            assert len(image.tags) == 1
            assert image.tags[0] == image_info.get_target_complete_name()


if __name__ == '__main__':
    unittest.main()
