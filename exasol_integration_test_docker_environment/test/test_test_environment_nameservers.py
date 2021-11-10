import unittest


from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.test.utils.utils import close_environments
from exasol_integration_test_docker_environment.testing import utils


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

    @classmethod
    def tearDownClass(cls):
        close_environments(cls.test_environment)

    def assert_nameserver(self, nameservers: str):
        with ContextDockerClient() as docker_client:
            containers = [c.name for c in docker_client.containers.list() if self.docker_environment_name in c.name]
            db_container = [c for c in containers if "db_container" in c]
            exit_result = docker_client.containers.get(db_container[0]).exec_run("cat /exa/etc/EXAConf")
            output = exit_result[1].decode("UTF-8")
            if output == '':
                exit_result = docker_client.containers.get(db_container[0]).exec_run("cat /exa/etc/EXAConf")
                output = exit_result[1].decode("UTF-8")
                return_code = exit_result[0]
            return_code = exit_result[0]
            self.assertEquals(return_code, 0)
            self.assertIn("NameServers = %s" % nameservers, output)

    def test_no_nameserver(self):
        self.docker_environment_name = "test_no_nameserver"
        on_host_docker_environment, google_cloud_docker_environment = \
            self.test_environment.spawn_docker_test_environment(self.docker_environment_name)
        self.assert_nameserver("")
        close_environments(on_host_docker_environment, google_cloud_docker_environment)

    def test_single_nameserver(self):
        self.docker_environment_name = "test_single_nameserver"
        on_host_docker_environment, google_cloud_docker_environment = \
            self.test_environment.spawn_docker_test_environment(self.docker_environment_name,
                                                                [
                                                                    "--nameserver", "'8.8.8.8'",
                                                                ])
        self.assert_nameserver("8.8.8.8")
        close_environments(on_host_docker_environment, google_cloud_docker_environment)

    def test_multiple_nameserver(self):
        self.docker_environment_name = "test_multiple_nameserver"
        on_host_docker_environment, google_cloud_docker_environment = \
            self.test_environment.spawn_docker_test_environment(self.docker_environment_name,
                                                                [
                                                                    "--nameserver", "'8.8.8.8'",
                                                                    "--nameserver", "'8.8.8.9'",
                                                                ])
        self.assert_nameserver("8.8.8.8,8.8.8.9")
        close_environments(on_host_docker_environment, google_cloud_docker_environment)

    # def test_invalid_db_mem_size(self):
    #     self.docker_environment_name = "test_invalid_db_mem_size"
    #     with self.assertRaises(Exception) as context:
    #         on_host_docker_environment, google_cloud_docker_environment = \
    #             self.test_environment.spawn_docker_test_environment(self.docker_environment_name,
    #                                                                # ["--db-mem-size", "'999 MiB'"])
    #     close_environments(on_host_docker_environment, google_cloud_docker_environment)


if __name__ == '__main__':
    unittest.main()
