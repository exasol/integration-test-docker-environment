import unittest
from sys import stderr
from typing import List

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing.exaslct_test_environment import (
    ExaslctTestEnvironment,
)


class TestEnvironmentVariable(unittest.TestCase):
    """
    Deprecated. Replaced by "./test/integration/test_api_test_environment_environment_variable.py"
    """

    @classmethod
    def setUpClass(cls):
        print(f"SetUp {cls.__name__}", file=stderr)
        cls.test_environment = ExaslctTestEnvironment(
            cls,
            utils.INTEGRATION_TEST_DOCKER_ENVIRONMENT_DEFAULT_BIN,
            clean_images_at_close=False,
        )

    @classmethod
    def tearDownClass(cls):
        utils.close_environments(cls.test_environment)

    def assert_env_variable(
        self, env_variables: list[str], docker_environment_name: str
    ):
        with ContextDockerClient() as docker_client:
            containers = [
                c.name
                for c in docker_client.containers.list()
                if docker_environment_name in c.name
            ]
            db_container = [c for c in containers if "db_container" in c]
            exit_result = docker_client.containers.get(db_container[0]).exec_run("env")
            output = exit_result[1].decode("UTF-8")
            return_code = exit_result[0]
            self.assertEqual(return_code, 0)
            for env_variable in env_variables:
                self.assertIn(env_variable, output)

    def test_env_variable(self):
        docker_environment_name = "test_env_variable"
        env_variable = "ABC=123"
        with self.test_environment.spawn_docker_test_environments(
            docker_environment_name, ["--docker-environment-variable", env_variable]
        ):
            self.assert_env_variable([env_variable], docker_environment_name)

    def test_multiple_env_variables(self):
        docker_environment_name = "test_env_variable"
        env_variables = ["ABC=123", "DEF=456"]
        with self.test_environment.spawn_docker_test_environments(
            docker_environment_name,
            [
                p
                for env_variable in env_variables
                for p in ("--docker-environment-variable", env_variable)
            ],
        ):
            self.assert_env_variable(env_variables, docker_environment_name)


if __name__ == "__main__":
    unittest.main()
