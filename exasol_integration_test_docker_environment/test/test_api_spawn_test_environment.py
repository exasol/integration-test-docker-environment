import unittest
from sys import stderr

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing.api_test_environment import ApiTestEnvironment


class APISpawnTestEnvironmentTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print(f"SetUp {cls.__name__}", file=stderr)
        # We can't use start-test-env. because it only mounts ./ and
        # doesn't work with --build_ouput-directory
        cls.test_environment = ApiTestEnvironment(cls)
        cls.docker_environment_name = cls.__name__
        cls.spawned_docker_test_environments = \
            cls.test_environment.spawn_docker_test_environment(name=cls.docker_environment_name)

    @classmethod
    def tearDownClass(cls):
        utils.close_environments(cls.spawned_docker_test_environments, cls.test_environment)

    def test_all_containers_started(self):
        with ContextDockerClient() as docker_client:
            containers = [c.name for c in docker_client.containers.list() if self.docker_environment_name in c.name]
            self.assertEqual(len(containers), 2,
                             f"Not exactly 2 containers in {containers}.")
            db_container = [c for c in containers if "db_container" in c]
            self.assertEqual(len(db_container), 1,
                             f"Found no db container in {containers}.")
            test_container = [c for c in containers if "test_container" in c]
            self.assertEqual(len(test_container), 1,
                             f"Found no test container in {containers}.")

    def test_docker_available_in_test_container(self):
        environment_info = self.spawned_docker_test_environments.environment_info
        with ContextDockerClient() as docker_client:
            test_container = docker_client.containers.get(environment_info.test_container_info.container_name)
            exit_result = test_container.exec_run("docker ps")
            exit_code = exit_result[0]
            output = exit_result[1]
            self.assertEqual(exit_code, 0,
                             f"Error while executing 'docker ps' in test container got output\n {output}.")

    def test_db_container_available(self):
        environment_info = self.spawned_docker_test_environments.environment_info
        with ContextDockerClient() as docker_client:
            db_container = docker_client.containers.get(environment_info.database_info.container_info.container_name)
            exit_result = db_container.exec_run("ls /exa")
            exit_code = exit_result[0]
            output = exit_result[1]
            self.assertEqual(exit_code, 0,
                             f"Error while executing 'ls /exa' in db container got output\n {output}.")

    def test_db_available(self):
        environment_info = self.spawned_docker_test_environments.environment_info
        with ContextDockerClient() as docker_client:
            test_container = docker_client.containers.get(environment_info.test_container_info.container_name)
            exit_result = test_container.exec_run(self.create_db_connection_command())
            exit_code = exit_result[0]
            output = exit_result[1]
            self.assertEqual(exit_code, 0,
                             f"Error while executing 'exaplus' in test container got output\n {output}.")

    def create_db_connection_command(self):
        spawned_docker_test_environments = self.spawned_docker_test_environments
        username = spawned_docker_test_environments.db_username
        password = spawned_docker_test_environments.db_password
        db_host = spawned_docker_test_environments.environment_info.database_info.host
        db_port = spawned_docker_test_environments.environment_info.database_info.db_port
        connection_options = f"-c '{db_host}:{db_port}' -u '{username}' -p '{password}'"
        cmd = f"""$EXAPLUS {connection_options}  -sql 'select 1;' -jdbcparam 'validateservercertificate=0'"""
        bash_cmd = f"""bash -c "{cmd}" """
        return bash_cmd


if __name__ == '__main__':
    unittest.main()
