import unittest

import docker

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.test.utils.utils import close_environments
from exasol_integration_test_docker_environment.testing import utils


class DockerTestEnvironmentDBDiskSizeTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print(f"SetUp {cls.__name__}")
        # We can't use start-test-env. because it only mounts ./ and
        # doesn't work with --build_ouput-directory
        cls.test_environment = \
            utils.ExaslctTestEnvironment(
                cls,
                utils.INTEGRATION_TEST_DOCKER_ENVIRONMENT_DEFAULT_BIN,
                clean_images_at_close=False)

    @classmethod
    def tearDownClass(cls):
        close_environments(cls.test_environment)

    def setUp(self) -> None:
        self.docker_envs = ()

    def tearDown(self):
        close_environments(*self.docker_envs)

    def assert_disk_size(self, size: str):
        with ContextDockerClient() as docker_client:
            containers = [c.name for c in docker_client.containers.list() if self.docker_environment_name in c.name]
            db_container = [c for c in containers if "db_container" in c]
            exit_result = docker_client.containers.get(db_container[0]).exec_run("cat /exa/etc/EXAConf")
            output = exit_result[1].decode("UTF-8")
            return_code = exit_result[0]
            if output == '':
                exit_result = docker_client.containers.get(db_container[0]).exec_run("cat /exa/etc/EXAConf")
                output = exit_result[1].decode("UTF-8")
                return_code = exit_result[0]
            self.assertEqual(return_code, 0)
            self.assertIn(" Size = %s" % size, output)

    def test_default_db_disk_size(self):
        self.docker_environment_name = "test_default_db_disk_size"
        self.docker_envs = self.test_environment.spawn_docker_test_environment(self.docker_environment_name)
        self.assert_disk_size("2 GiB")

    def test_smallest_valid_db_disk_size(self):
        self.docker_environment_name = "test_smallest_valid_db_disk_size"
        self.docker_envs = self.test_environment.spawn_docker_test_environment(self.docker_environment_name,
                                                                               ["--db-disk-size", "'100 MiB'"])
        self.assert_disk_size("100 MiB")

    def test_invalid_db_mem_size(self):
        self.docker_environment_name = "test_invalid_db_disk_size"
        with self.assertRaises(Exception) as context:
            self.docker_envs = \
                self.test_environment.spawn_docker_test_environment(self.docker_environment_name,
                                                                    ["--db-disk-size", "'90 MiB'"])


if __name__ == '__main__':
    unittest.main()
