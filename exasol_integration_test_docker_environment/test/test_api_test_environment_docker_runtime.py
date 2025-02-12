import subprocess
import unittest

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.models import api_errors
from exasol_integration_test_docker_environment.test.get_test_container_content import (
    get_test_container_content,
)
from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing.api_test_environment import (
    ApiTestEnvironment,
)


def assert_container_runtime(self, container_name, expected_runtime):
    with ContextDockerClient() as docker_client:
        container = docker_client.containers.get(container_name)
        container.reload()
        actual_runtime = container.attrs["HostConfig"]["Runtime"]
        self.assertEqual(
            actual_runtime,
            expected_runtime,
            f"{container_name} has the wrong runtime expected {expected_runtime} got {actual_runtime}.",
        )


def get_default_docker_runtime():
    with ContextDockerClient() as docker_client:
        tmp_container = docker_client.containers.create("ubuntu:22.04", "echo")
        try:
            tmp_container.reload()
            default_docker_runtime = tmp_container.attrs["HostConfig"]["Runtime"]
        finally:
            tmp_container.remove(force=True)
        return default_docker_runtime


class DockerTestEnvironmentDockerRuntimeNoRuntimeGivenTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print(f"SetUp {cls.__name__}")
        cls.test_environment = ApiTestEnvironment(cls)
        cls.docker_environment_name = "test_no_runtime_given"
        cls.environment = (
            cls.test_environment.spawn_docker_test_environment_with_test_container(
                name=cls.docker_environment_name,
                test_container_content=get_test_container_content(),
            )
        )
        cls.default_docker_runtime = get_default_docker_runtime()

    @classmethod
    def tearDownClass(cls):
        utils.close_environments(cls.environment, cls.test_environment)

    def test_test_container_runtime(self):
        environment_info = self.environment.environment_info
        test_container_name = environment_info.test_container_info.container_name
        assert_container_runtime(self, test_container_name, self.default_docker_runtime)

    def test_database_container_runtime(self):
        environment_info = self.environment.environment_info
        database_container_name = (
            environment_info.database_info.container_info.container_name
        )
        assert_container_runtime(
            self, database_container_name, self.default_docker_runtime
        )


class DockerTestEnvironmentDockerRuntimeDefaultRuntimeGivenTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print(f"SetUp {cls.__name__}")
        cls.test_environment = ApiTestEnvironment(cls)
        cls.default_docker_runtime = get_default_docker_runtime()
        cls.docker_environment_name = "test_default_runtime_given"
        cls.environment = (
            cls.test_environment.spawn_docker_test_environment_with_test_container(
                cls.docker_environment_name,
                test_container_content=get_test_container_content(),
                additional_parameter={
                    "docker_runtime": cls.default_docker_runtime,
                },
            )
        )

    @classmethod
    def tearDownClass(cls):
        utils.close_environments(cls.environment, cls.test_environment)

    def test_test_container_runtime(self):
        environment_info = self.environment.environment_info
        test_container_name = environment_info.test_container_info.container_name
        assert_container_runtime(self, test_container_name, self.default_docker_runtime)

    def test_database_container_runtime(self):
        environment_info = self.environment.environment_info
        database_container_name = (
            environment_info.database_info.container_info.container_name
        )
        assert_container_runtime(
            self, database_container_name, self.default_docker_runtime
        )


class DockerTestEnvironmentDockerRuntimeInvalidRuntimeGivenTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print(f"SetUp {cls.__name__}")
        cls.test_environment = ApiTestEnvironment(cls)
        cls.docker_environment_name = "test_default_runtime_given"

    @classmethod
    def tearDownClass(cls):
        utils.close_environments(cls.test_environment)

    def test_docker_environment_not_available(self):
        exception_thrown = False
        spawn_docker_test_environments_successful = False
        try:
            environment = (
                self.test_environment.spawn_docker_test_environment_with_test_container(
                    self.docker_environment_name,
                    test_container_content=get_test_container_content(),
                    additional_parameter={
                        "docker_runtime": "AAAABBBBCCCC_INVALID_RUNTIME_111122223333"
                    },
                )
            )
            spawn_docker_test_environments_successful = True
            utils.close_environments(environment)
        except api_errors.TaskRuntimeError:
            exception_thrown = True
        self.assertFalse(spawn_docker_test_environments_successful)
        self.assertTrue(exception_thrown)


if __name__ == "__main__":
    unittest.main()
