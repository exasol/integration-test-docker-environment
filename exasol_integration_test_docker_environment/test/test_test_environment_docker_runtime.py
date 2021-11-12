import unittest

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing.exaslct_test_environment import ExaslctTestEnvironment


def assert_container_runtime(self, container_name, expected_runtime):
    on_host_docker_environment = self.spawned_docker_test_environments.on_host_docker_environment
    with ContextDockerClient() as docker_client:
        try:
            container = docker_client.containers.get(container_name)
            container.reload()
            actual_runtime = container.attrs['HostConfig']['Runtime']
        except Exception as e:
            startup_log = on_host_docker_environment.completed_process.stdout.decode("utf8")
            raise Exception(f"Startup log: {startup_log}") from e
        self.assertEqual(actual_runtime, expected_runtime,
                         f"{container_name} has the wrong runtime expected {expected_runtime} got {actual_runtime}."
                         f"\n Startup log is "
                         f"{on_host_docker_environment.completed_process.stdout.decode('utf8')}")


def get_default_docker_runtime():
    with ContextDockerClient() as docker_client:
        tmp_container = docker_client.containers.create("ubuntu:18.04", "echo")
        try:
            tmp_container.reload()
            default_docker_runtime = tmp_container.attrs['HostConfig']['Runtime']
        finally:
            tmp_container.remove(force=True)
        return default_docker_runtime


class DockerTestEnvironmentDockerRuntimeNoRuntimeGivenTest(unittest.TestCase):

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
        cls.docker_environment_name = "test_no_runtime_given"
        cls.spawned_docker_test_environments = \
            cls.test_environment.spawn_docker_test_environments(cls.docker_environment_name)
        cls.default_docker_runtime = get_default_docker_runtime()

    @classmethod
    def tearDownClass(cls):
        cls.spawned_docker_test_environments.close()
        utils.close_environments(cls.test_environment)

    def test_test_container_runtime(self):
        try:
            environment_info = self.spawned_docker_test_environments.on_host_docker_environment.environment_info
            test_container_name = environment_info.test_container_info.container_name
        except Exception as e:
            startup_log = self.spawned_docker_test_environments\
                .on_host_docker_environment.completed_process.stdout.decode("utf8")
            raise Exception(f"Startup log: {startup_log}") from e
        assert_container_runtime(self, test_container_name, self.default_docker_runtime)

    def test_database_container_runtime(self):
        try:
            environment_info = self.spawned_docker_test_environments.on_host_docker_environment.environment_info
            database_container_name = environment_info.database_info.container_info.container_name
        except Exception as e:
            startup_log = \
                self.spawned_docker_test_environments.on_host_docker_environment.completed_process.stdout.decode("utf8")
            raise Exception(f"Startup log: {startup_log}") from e
        assert_container_runtime(self, database_container_name, self.default_docker_runtime)


class DockerTestEnvironmentDockerRuntimeDefaultRuntimeGivenTest(unittest.TestCase):

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
        cls.default_docker_runtime = get_default_docker_runtime()
        cls.docker_environment_name = "test_default_runtime_given"
        cls.spawned_docker_test_environments = cls.test_environment.spawn_docker_test_environments(
                cls.docker_environment_name,
                additional_parameter=["--docker-runtime", cls.default_docker_runtime])

    @classmethod
    def tearDownClass(cls):
        cls.spawned_docker_test_environments.close()
        utils.close_environments(cls.google_cloud_docker_environment)

    def test_test_container_runtime(self):
        on_host_docker_environment = self.spawned_docker_test_environments.on_host_docker_environment
        try:
            environment_info = on_host_docker_environment.environment_info
            test_container_name = environment_info.test_container_info.container_name
        except Exception as e:
            startup_log = on_host_docker_environment.completed_process.stdout.decode("utf8")
            raise Exception(f"Startup log: {startup_log}") from e
        assert_container_runtime(self, test_container_name, self.default_docker_runtime)

    def test_database_container_runtime(self):
        on_host_docker_environment = self.spawned_docker_test_environments.on_host_docker_environment
        try:
            environment_info = on_host_docker_environment.environment_info
            database_container_name = environment_info.database_info.container_info.container_name
        except Exception as e:
            startup_log = on_host_docker_environment.completed_process.stdout.decode("utf8")
            raise Exception(f"Startup log: {startup_log}") from e
        assert_container_runtime(self, database_container_name, self.default_docker_runtime)


class DockerTestEnvironmentDockerRuntimeInvalidRuntimeGivenTest(unittest.TestCase):

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
        cls.default_docker_runtime = get_default_docker_runtime()
        cls.docker_environment_name = "test_default_runtime_given"
        cls.docker_environments = ()
        try:
            cls.spawned_docker_test_environments = cls.test_environment.spawn_docker_test_environments(
                    cls.docker_environment_name,
                    additional_parameter=["--docker-runtime", "AAAABBBBCCCC_INVALID_RUNTIME_111122223333"])
        except Exception as e:
            pass

    @classmethod
    def tearDownClass(cls):
        cls.spawned_docker_test_environments.close()
        cls.test_environment.close()

    def test_docker_environment_not_available(self):
        self.assertFalse("on_host_docker_environment" in self.__dict__)


if __name__ == '__main__':
    unittest.main()
