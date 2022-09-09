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
            cls.test_environment.spawn_docker_test_environments(name=cls.docker_environment_name)

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

    def test_db_available(self):
        environment_info = self.spawned_docker_test_environments.on_host_docker_environment
        db_container_name = environment_info.environment_info.database_info.container_info.container_name
        with ContextDockerClient() as docker_client:
            db_container = docker_client.containers.get(db_container_name)
            exit_result = db_container.exec_run(self.create_db_connection_command())
            exit_code = exit_result[0]
            output = exit_result[1]
            self.assertEqual(exit_code, 0,
                             f"Error while executing 'exaplus' in test container got output\n {output}.")

    def create_db_connection_command(self):
        spawned_docker_test_environments = self.spawned_docker_test_environments
        username = spawned_docker_test_environments.on_host_docker_environment.db_username
        password = spawned_docker_test_environments.on_host_docker_environment.db_password
        db_host = spawned_docker_test_environments.on_host_docker_environment.environment_info.database_info.host
        db_port = spawned_docker_test_environments.on_host_docker_environment.environment_info.database_info.db_port
        db_version = spawned_docker_test_environments.on_host_docker_environment.docker_db_image_version
        connection_options = f"-c '{db_host}:{db_port}' -u '{username}' -p '{password}'"
        exaplus = f"/usr/opt/EXASuite-7/EXASolution-{db_version}/bin/Console/exaplus"
        cmd = f"""{exaplus} {connection_options}  -sql 'select 1;' -jdbcparam 'validateservercertificate=0'"""
        bash_cmd = f"""bash -c "{cmd}" """
        return bash_cmd


if __name__ == '__main__':
    unittest.main()
