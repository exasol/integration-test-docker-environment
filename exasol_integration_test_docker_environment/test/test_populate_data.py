import unittest
from pathlib import Path, PurePath
from sys import stderr

import luigi

from exasol_integration_test_docker_environment.lib.api.common import generate_root_task
from exasol_integration_test_docker_environment.lib.data.test_container_content_description import \
    TestContainerRuntimeMapping
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.test_environment.database_setup.populate_data import \
    PopulateTestDataToDatabase
from exasol_integration_test_docker_environment.test.get_test_container_content import get_test_container_content
from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing.api_test_environment import ApiTestEnvironment


class TestDataPopulateData(PopulateTestDataToDatabase):

    def get_data_path_within_test_container(self) -> PurePath:
        return PurePath("/test_data")

    def get_data_file_within_data_path(self) -> PurePath:
        return PurePath("import.sql")


class TestPopulateData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print(f"SetUp {cls.__name__}", file=stderr)
        cls.test_environment = ApiTestEnvironment(cls)
        cls.docker_environment_name = cls.__name__
        test_data_folder = Path(__file__).parent / "resources" / "test_data"
        test_container_runtime_mapping = TestContainerRuntimeMapping(source=test_data_folder, target="/test_data")
        test_container_content = get_test_container_content((test_container_runtime_mapping,))
        cls.environment = \
            cls.test_environment.spawn_docker_test_environment_with_test_container(
                name=cls.docker_environment_name,
                test_container_content=test_container_content
            )

    @classmethod
    def tearDownClass(cls):
        utils.close_environments(cls.environment, cls.test_environment)

    def _populate_data(self, reuse=False):
        task = generate_root_task(task_class=TestDataPopulateData,
                                  environment_name=self.environment.name,
                                  db_user=self.environment.db_username,
                                  db_password=self.environment.db_password,
                                  bucketfs_write_password=self.environment.bucketfs_password,
                                  test_environment_info=self.environment.environment_info,
                                  )
        try:
            success = luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
            if not success:
                raise Exception("Task failed")
        except Exception as e:
            task.cleanup(False)
            raise RuntimeError("Error uploading test file.") from e

    def setUp(self) -> None:
        self._execute_sql_on_db("DROP SCHEMA IF EXISTS TEST CASCADE;")

    def _execute_sql_on_db(self, sql: str) -> str:
        with ContextDockerClient() as docker_client:
            test_container = docker_client.containers.get(self.environment.environment_info.
                                                          test_container_info.container_name)
            db_info = self.environment.environment_info.database_info
            db_user_name = self.environment.db_username
            db_password = self.environment.db_password
            cmd = f"$EXAPLUS -x -q -c '{db_info.host}:{db_info.db_port}' " \
                  f"-u '{db_user_name}' -p '{db_password}' -sql '{sql}' " \
                  f"-jdbcparam 'validateservercertificate=0'"

            bash_cmd = f"""bash -c "{cmd}" """
            exit_code, output = test_container.exec_run(cmd=bash_cmd)

            if exit_code != 0:
                raise RuntimeError(f"Error executing sql. Output is {output}")

        return output.decode("utf-8")

    def test_populate_data(self):
        self._populate_data()
        result = self._execute_sql_on_db("SELECT count(*) FROM TEST.ENGINETABLE;")
        expected_result = '\nCOUNT(*)             \n---------------------\n                  100\n\n'
        self.assertEquals(result, expected_result)

    def test_populate_twice_throws_exception(self):
        self._populate_data()
        exception_thrown = False
        try:
            self._populate_data()
        except RuntimeError:
            exception_thrown = True
        self.assertTrue(exception_thrown)


if __name__ == '__main__':
    unittest.main()
