import unittest
from pathlib import Path

import docker

from src.test import utils


class DockerTestEnvironmentTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print(f"SetUp {cls.__name__}")
        # We can't use start-test-env. because it only mounts ./ and
        # doesn't work with --build_ouput-directory
        cls.test_environment = \
            utils.ExaslctTestEnvironment(
                cls,
                "./start-test-env-without-docker-runner",
                clean_images_at_close=False)
        # TODO cls.test_environment.clean_images()
        cls.docker_environment_name = cls.__name__
        cls.on_host_docker_environment, cls.google_cloud_docker_environment = \
            cls.test_environment.spawn_docker_test_environment(cls.docker_environment_name)

    def setUp(self):
        self.client = docker.from_env()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.on_host_docker_environment.close()
        except Exception as e:
            print(e)
        try:
            cls.google_cloud_docker_environment.close()
        except Exception as e:
            print(e)
        try:
            cls.test_environment.close()
        except Exception as e:
            print(e)

    def tearDown(self):
        self.client.close()

    def test_all_containers_started(self):
        containers = [c.name for c in self.client.containers.list() if self.docker_environment_name in c.name]
        self.assertEqual(len(containers), 2,
                         f"Not exactly 2 containers in {containers}.\nStartup log was: {self.on_host_docker_environment.completed_process.stdout.decode('utf8')}")
        db_container = [c for c in containers if "db_container" in c]
        self.assertEqual(len(db_container), 1,
                         f"Found no db container in {containers}.\nStartup log was: {self.on_host_docker_environment.completed_process.stdout.decode('utf8')}")
        test_container = [c for c in containers if "test_container" in c]
        self.assertEqual(len(test_container), 1,
                         f"Found no test container in {containers}.\nStartup log was: {self.on_host_docker_environment.completed_process.stdout.decode('utf8')}")

    def test_docker_available_in_test_container(self):
        containers = [c.name for c in self.client.containers.list() if self.docker_environment_name in c.name]
        test_container = [c for c in containers if "test_container" in c]
        exit_result = self.client.containers.get(test_container[0]).exec_run("docker ps")
        exit_code = exit_result[0]
        output = exit_result[1]
        self.assertEqual(exit_code, 0,
                         f"Error while executing 'docker ps' in test container got output\n {output}.\nStartup log was: {self.on_host_docker_environment.completed_process.stdout.decode('utf8')}")

    def test_envrionment_info_available(self):
        temp_dir_glob = list(Path(self.test_environment.temp_dir).glob("**/*"))
        path_filter = f"cache/environments/{self.on_host_docker_environment.name}"
        actual_environment_infos = sorted([path.name
                                           for path in temp_dir_glob
                                           if path_filter in str(path) and "environment_info" in path.name])
        expected_environment_infos = sorted(["environment_info.sh", "environment_info.conf", "environment_info.json"])
        self.assertEqual(actual_environment_infos, expected_environment_infos,
                         f"Did not found environment_info files on host.\nStartup log was: {self.on_host_docker_environment.completed_process.stdout.decode('utf8')}")


if __name__ == '__main__':
    unittest.main()
