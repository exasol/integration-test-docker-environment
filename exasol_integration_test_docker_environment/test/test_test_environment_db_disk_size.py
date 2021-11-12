import unittest

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing.exaslct_test_environment import ExaslctTestEnvironment


class DockerTestEnvironmentDBDiskSizeTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print(f"SetUp {cls.__name__}")
        # We can't use start-test-env. because it only mounts ./ and
        # doesn't work with --build_ouput-directory
        cls.test_environment = \
            ExaslctTestEnvironment(
                cls,
                utils.INTEGRATION_TEST_DOCKER_ENVIRONMENT_DEFAULT_BIN,
                clean_images_at_close=False)

    @classmethod
    def tearDownClass(cls):
        cls.test_environment.close()

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
        with self.test_environment.spawn_docker_test_environments(self.docker_environment_name):
            self.assert_disk_size("2 GiB")

    def test_smallest_valid_db_disk_size(self):
        self.docker_environment_name = "test_smallest_valid_db_disk_size"
        with self.test_environment.spawn_docker_test_environments(self.docker_environment_name,
                                                                  ["--db-disk-size", "'100 MiB'"]):
            self.assert_disk_size("100 MiB")

    def test_invalid_db_mem_size(self):
        self.docker_environment_name = "test_invalid_db_disk_size"
        with self.assertRaises(Exception) as context:
            with self.test_environment.spawn_docker_test_environments(self.docker_environment_name,
                                                                      ["--db-disk-size", "'90 MiB'"]):
                pass


if __name__ == '__main__':
    unittest.main()
