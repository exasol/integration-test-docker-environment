import unittest

import docker

from src.test import utils


class DockerTestEnvironmentDBDiskSizeTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print(f"SetUp {cls.__name__}")
        cls.test_environment = utils.ExaslctTestEnvironment(cls, "./start-test-env",
                                                            clean_images_at_close=False)

    def setUp(self):
        self.client = docker.from_env()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.test_environment.close()
        except Exception as e:
            print(e)

    def tearDown(self):
        try:
            self.on_host_docker_environment.close()
        except Exception as e:
            print(e)
        try:
            self.google_cloud_docker_environment.close()
        except Exception as e:
            print(e)
        self.client.close()

    def assert_disk_size(self, size:str):
        containers = [c.name for c in self.client.containers.list() if self.docker_environment_name in c.name]
        db_container = [c for c in containers if "db_container" in c]
        exit_result = self.client.containers.get(db_container[0]).exec_run("cat /exa/etc/EXAConf")
        output = exit_result[1].decode("UTF-8")
        return_code = exit_result[0]
        if output == '':
            exit_result = self.client.containers.get(db_container[0]).exec_run("cat /exa/etc/EXAConf")
            output = exit_result[1].decode("UTF-8")
            return_code = exit_result[0]
        self.assertEquals(return_code,0)
        self.assertIn(" Size = %s"%size,output)


    def test_default_db_disk_size(self):
        self.docker_environment_name = "test_default_db_disk_size"
        self.on_host_docker_environment, self.google_cloud_docker_environment = \
            self.test_environment.spawn_docker_test_environment(self.docker_environment_name)
        self.assert_disk_size("2 GiB")

    def test_smallest_valid_db_disk_size(self):
        self.docker_environment_name = "test_smallest_valid_db_disk_size"
        self.on_host_docker_environment, self.google_cloud_docker_environment = \
            self.test_environment.spawn_docker_test_environment(self.docker_environment_name, ["--db-disk-size","'100 MiB'"])
        self.assert_disk_size("100 MiB")
    
    def test_invalid_db_mem_size(self):
        self.docker_environment_name = "test_invalid_db_disk_size"
        with self.assertRaises(Exception) as context:
            self.on_host_docker_environment, self.google_cloud_docker_environment = \
                self.test_environment.spawn_docker_test_environment(self.docker_environment_name, ["--db-disk-size","'90 MiB'"])


if __name__ == '__main__':
    unittest.main()
