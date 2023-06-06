import unittest
from typing import List

import docker.models.containers

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.test_environment.database_setup.find_exaplus_in_db_container import \
    find_exaplus
from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing.exaslct_test_environment import ExaslctTestEnvironment


class DockerTestEnvironmentTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print(f"SetUp {cls.__name__}")
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
        def assert_exactly_one(prefix: str, all: List[str], selected: List[str] = None):
            selected = selected if selected is None else all
            log = self.spawned_docker_test_environments \
                      .on_host_docker_environment \
                      .completed_process.stdout.decode('utf8')
            self.assertEqual(len(selected), 1, f"{prefix} in {all}.\nStartup log was: {log}")
        with ContextDockerClient() as docker_client:
            containers = [c.name for c in docker_client.containers.list() if self.docker_environment_name in c.name]
            assert_exactly_one("Not exactly 1 container", containers)
            db_containers = [c for c in containers if "db_container" in c]
            assert_exactly_one("Found no db container", containers, db_containers)

    def test_db_available(self):
        db_container_name = self.spawned_docker_test_environments \
                                .on_host_docker_environment \
                                .environment_info \
                                .database_info \
                                .container_info \
                                .container_name
        with ContextDockerClient() as docker_client:
            db_container = docker_client.containers.get(db_container_name)
            command = self.db_connection_command(db_container))
            exit_code, output = db_container.exec_run(command)
            self.assertEqual(
                exit_code,
                0,
                f"Error while executing 'exaplus' in test container. Got output:\n {output}",
            )

    def db_connection_command(self, db_container: docker.models.containers.Container):
        on_host = self.spawned_docker_test_environments.on_host_docker_environment
        db_info = on_host.environment_info.database_info
        # unused: db_version = on_host.docker_db_image_version
        connection_options = (
            f"-c '{db_info.host}:{db_info.ports.database}' "
            f"-u '{on_host.db_username}' "
            f"-p '{on_host.db_password}'"
        )
        exaplus = find_exaplus(db_container)
        command = (
            f"{exaplus} {connection_options} "
            "-sql 'select 1;' "
            "-jdbcparam 'validateservercertificate=0'"
        )
        return f'bash -c "{command}" '


if __name__ == '__main__':
    unittest.main()
