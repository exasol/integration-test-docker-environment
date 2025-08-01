import tempfile
import unittest
from pathlib import Path
from sys import stderr
from typing import Optional

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.models.data.environment_info import (
    EnvironmentInfo,
)
from exasol_integration_test_docker_environment.lib.models.data.test_container_content_description import (
    TestContainerRuntimeMapping,
)
from exasol_integration_test_docker_environment.test.get_test_container_content import (
    get_test_container_content,
)
from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing.api_test_environment import (
    ApiTestEnvironment,
)
from exasol_integration_test_docker_environment.testing.utils import (
    find_docker_container_names,
)


class APISpawnTestEnvironmentTest(unittest.TestCase):
    """
    Deprecated. Replaced by "./test/integration/test_api_test_environment.py"
    """

    @classmethod
    def setUpClass(cls):
        print(f"SetUp {cls.__name__}", file=stderr)
        cls.test_environment = ApiTestEnvironment(cls)
        cls.docker_environment_name = cls.__name__
        cls.environment = (
            cls.test_environment.spawn_docker_test_environment_with_test_container(
                name=cls.docker_environment_name,
                test_container_content=get_test_container_content(),
            )
        )

    @classmethod
    def tearDownClass(cls):
        utils.close_environments(cls.environment, cls.test_environment)

    def test_all_containers_started(self):
        containers = find_docker_container_names(self.docker_environment_name)
        self.assertEqual(
            len(containers), 2, f"Not exactly 2 containers in {containers}."
        )
        db_container = [c for c in containers if "db_container" in c]
        self.assertEqual(
            len(db_container), 1, f"Found no db container in {containers}."
        )
        test_container = [c for c in containers if "test_container" in c]
        self.assertEqual(
            len(test_container), 1, f"Found no test container in {containers}."
        )

    def test_docker_available_in_test_container(self):
        environment_info = self.environment.environment_info
        with ContextDockerClient() as docker_client:
            test_container = docker_client.containers.get(
                environment_info.test_container_info.container_name
            )
            exit_result = test_container.exec_run("docker ps")
            exit_code = exit_result[0]
            output = exit_result[1]
            self.assertEqual(
                exit_code,
                0,
                f"Error while executing 'docker ps' in test container got output\n {output}.",
            )

    def test_db_container_available(self):
        environment_info = self.environment.environment_info
        with ContextDockerClient() as docker_client:
            db_container = docker_client.containers.get(
                environment_info.database_info.container_info.container_name
            )
            exit_result = db_container.exec_run("ls /exa")
            exit_code = exit_result[0]
            output = exit_result[1]
            self.assertEqual(
                exit_code,
                0,
                f"Error while executing 'ls /exa' in db container got output\n {output}.",
            )

    def test_db_available(self):
        environment_info = self.environment.environment_info
        with ContextDockerClient() as docker_client:
            test_container = docker_client.containers.get(
                environment_info.test_container_info.container_name
            )
            exit_result = test_container.exec_run(self.create_db_connection_command())
            exit_code = exit_result[0]
            output = exit_result[1]
            self.assertEqual(
                exit_code,
                0,
                f"Error while executing 'exaplus' in test container got output\n {output}.",
            )

    def create_db_connection_command(self):
        spawned_docker_test_environments = self.environment
        username = spawned_docker_test_environments.db_username
        password = spawned_docker_test_environments.db_password
        db_host = spawned_docker_test_environments.environment_info.database_info.host
        db_port = (
            spawned_docker_test_environments.environment_info.database_info.ports.database
        )
        connection_options = f"-c '{db_host}:{db_port}' -u '{username}' -p '{password}'"
        cmd = f"""$EXAPLUS {connection_options}  -sql 'select 1;' -jdbcparam 'validateservercertificate=0'"""
        bash_cmd = f"""bash -c "{cmd}" """
        return bash_cmd

    def test_build_mapping(self):
        environment_info = self.environment.environment_info
        with ContextDockerClient() as docker_client:
            test_container = docker_client.containers.get(
                environment_info.test_container_info.container_name
            )
            exit_code, output = test_container.exec_run("cat /test.text")
            self.assertEqual(exit_code, 0)
            self.assertEqual(output.decode("UTF-8"), "Empty File")


class APISpawnTestEnvironmentTestWithCustomRuntimeMapping(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print(f"SetUp {cls.__name__}", file=stderr)
        cls.test_environment = ApiTestEnvironment(cls)
        cls.docker_environment_name = cls.__name__

    @classmethod
    def tearDownClass(cls):
        utils.close_environments(cls.test_environment)

    def _assert_deployment_available(self, environment_info: EnvironmentInfo) -> None:
        with ContextDockerClient() as docker_client:
            assert environment_info.test_container_info
            test_container = docker_client.containers.get(
                environment_info.test_container_info.container_name
            )
            exit_code, output = test_container.exec_run("cat /test/test.txt")
            self.assertEqual(exit_code, 0)
            self.assertEqual(output.decode("utf-8"), "test")

    def _assert_deployment_not_shared(
        self, environment_info: EnvironmentInfo, temp_path: Path
    ):
        with ContextDockerClient() as docker_client:
            assert environment_info.test_container_info
            test_container = docker_client.containers.get(
                environment_info.test_container_info.container_name
            )
            exit_code, output = test_container.exec_run(
                "touch /test_target/test_new.txt"
            )
            self.assertEqual(exit_code, 0)
            local_path = temp_path / "test_new.txt"
            self.assertFalse(local_path.exists())

    def _get_test_mapping(
        self, temp_path: Path, deployment_target: Optional[str] = None
    ):
        with open(temp_path / "test.txt", "w") as f:
            f.write("test")
        return TestContainerRuntimeMapping(
            source=temp_path, target="/test", deployment_target=deployment_target
        )

    def test_runtime_mapping_without_deployment(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            mapping = self._get_test_mapping(Path(temp_dir))
            try:
                environment = self.test_environment.spawn_docker_test_environment_with_test_container(
                    name=self.docker_environment_name,
                    test_container_content=get_test_container_content(
                        runtime_mapping=(mapping,)
                    ),
                )
                environment_info = environment.environment_info
                self._assert_deployment_available(environment_info)
            finally:
                utils.close_environments(environment)

    def test_runtime_mapping_deployment(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            mapping = self._get_test_mapping(
                temp_path=temp_path, deployment_target="/test_target"
            )
            try:
                environment = self.test_environment.spawn_docker_test_environment_with_test_container(
                    name=self.docker_environment_name,
                    test_container_content=get_test_container_content(
                        runtime_mapping=(mapping,)
                    ),
                )
                environment_info = environment.environment_info
                self._assert_deployment_available(environment_info)
                self._assert_deployment_not_shared(environment_info, temp_path)

            finally:
                utils.close_environments(environment)


if __name__ == "__main__":
    unittest.main()
