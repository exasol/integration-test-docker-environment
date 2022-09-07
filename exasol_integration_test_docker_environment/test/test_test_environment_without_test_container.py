import unittest

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing.exaslct_test_environment import ExaslctTestEnvironment


class DockerTestEnvironmentTest(unittest.TestCase):

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
        # TODO cls.test_environment.clean_images()
        cls.docker_environment_name = cls.__name__
        cls.spawned_docker_test_environments = \
            cls.test_environment.spawn_docker_test_environments(name=cls.docker_environment_name,
                                                                additional_parameter=[
                                                                    "--deactivate-database-setup"
                                                                ])

    @classmethod
    def tearDownClass(cls):
        utils.close_environments(cls.spawned_docker_test_environments, cls.test_environment)

    def test_db_container_started(self):
        on_host_docker_environment = self.spawned_docker_test_environments.on_host_docker_environment
        with ContextDockerClient() as docker_client:
            containers = [c.name for c in docker_client.containers.list() if self.docker_environment_name in c.name]
            self.assertEqual(len(containers), 1,
                             f"Not exactly 1 container in {containers}.\nStartup log was: "
                             f"{on_host_docker_environment.completed_process.stdout.decode('utf8')}")
            db_container = [c for c in containers if "db_container" in c]
            self.assertEqual(len(db_container), 1,
                             f"Found no db container in {containers}.\nStartup log was: "
                             f"{on_host_docker_environment.completed_process.stdout.decode('utf8')}")


if __name__ == '__main__':
    unittest.main()
