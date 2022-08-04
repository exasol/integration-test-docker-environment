import unittest
from pathlib import Path

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing.api_test_environment import ApiTestEnvironment


class DockerAPITestEnvironmentTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print(f"SetUp {cls.__name__}")
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
        with ContextDockerClient() as docker_client:
            containers = [c.name for c in docker_client.containers.list() if self.docker_environment_name in c.name]
            test_container = [c for c in containers if "test_container" in c]
            exit_result = docker_client.containers.get(test_container[0]).exec_run("docker ps")
            exit_code = exit_result[0]
            output = exit_result[1]
            self.assertEqual(exit_code, 0,
                             f"Error while executing 'docker ps' in test container got output\n {output}.")

    def test_envrionment_info_available(self):
        on_host_docker_environment = self.spawned_docker_test_environments.on_host_docker_environment
        temp_dir_glob = list(Path(self.test_environment.temp_dir).glob("**/*"))
        path_filter = f"cache/environments/{on_host_docker_environment.name}"
        actual_environment_infos = sorted([path.name
                                           for path in temp_dir_glob
                                           if path_filter in str(path) and "environment_info" in path.name])
        expected_environment_infos = sorted(["environment_info.sh", "environment_info.conf", "environment_info.json"])
        self.assertEqual(actual_environment_infos, expected_environment_infos,
                         f"Did not found environment_info files on host.")


if __name__ == '__main__':
    unittest.main()
