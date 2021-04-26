import unittest

import docker

from exasol_integration_test_docker_environment.test import utils


class DockerTestEnvironmentDBMemSizeTest(unittest.TestCase):

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

    def setUp(self):
        self.client = docker.from_env()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.test_environment.close()
        except Exception as e:
            print(e)

    def tearDown(self):
        try:
            self.on_host_docker_environment.close()
        except Exception as e:
            print(e)
        try:
            self.google_cloud_docker_environment.close()
        except Exception as e:
            print(e)
        self.client.close()

    def assert_nameserver(self, nameservers: str):
        containers = [c.name for c in self.client.containers.list() if self.docker_environment_name in c.name]
        db_container = [c for c in containers if "db_container" in c]
        exit_result = self.client.containers.get(db_container[0]).exec_run("cat /exa/etc/EXAConf")
        output = exit_result[1].decode("UTF-8")
        if output == '':
            exit_result = self.client.containers.get(db_container[0]).exec_run("cat /exa/etc/EXAConf")
            output = exit_result[1].decode("UTF-8")
            return_code = exit_result[0]
        return_code = exit_result[0]
        self.assertEquals(return_code, 0)
        self.assertIn("NameServers = %s" % nameservers, output)

    def test_no_nameserver(self):
        self.docker_environment_name = "test_no_nameserver"
        self.on_host_docker_environment, self.google_cloud_docker_environment = \
            self.test_environment.spawn_docker_test_environment(self.docker_environment_name)
        self.assert_nameserver("")

    def test_single_nameserver(self):
        self.docker_environment_name = "test_single_nameserver"
        self.on_host_docker_environment, self.google_cloud_docker_environment = \
            self.test_environment.spawn_docker_test_environment(self.docker_environment_name,
                                                                [
                                                                    "--nameserver", "'8.8.8.8'",
                                                                ])
        self.assert_nameserver("8.8.8.8")

    def test_multiple_nameserver(self):
        self.docker_environment_name = "test_multiple_nameserver"
        self.on_host_docker_environment, self.google_cloud_docker_environment = \
            self.test_environment.spawn_docker_test_environment(self.docker_environment_name,
                                                                [
                                                                    "--nameserver", "'8.8.8.8'",
                                                                    "--nameserver", "'8.8.8.9'",
                                                                ])
        self.assert_nameserver("8.8.8.8,8.8.8.9")

    # def test_invalid_db_mem_size(self):
    #     self.docker_environment_name = "test_invalid_db_mem_size"
    #     with self.assertRaises(Exception) as context:
    #         self.on_host_docker_environment, self.google_cloud_docker_environment = \
    #             self.test_environment.spawn_docker_test_environment(self.docker_environment_name,
                                                                    # ["--db-mem-size", "'999 MiB'"])


if __name__ == '__main__':
    unittest.main()