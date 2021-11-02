import unittest

import docker
import luigi

from exasol_integration_test_docker_environment.lib.data.environment_type import EnvironmentType
from exasol_integration_test_docker_environment.lib.test_environment.spawn_test_environment import SpawnTestEnvironment
from exasol_integration_test_docker_environment.test.utils import process_spawn_utils
from exasol_integration_test_docker_environment.cli.common import set_docker_repository_config
from exasol_integration_test_docker_environment.test.utils import luigi_utils


class TestContainerReuseTest(unittest.TestCase):
    '''
    This test spawns a new test environment and, with parameters:
    * reuse_database_setup=True,
    * reuse_database=True,
    * reuse_test_container=True
    and verifies if the test data was populated to the docker db.
    '''

    def env_name(self):
        return self.__class__.__name__.lower()

    def setUp(self):
        self._client = docker.from_env()
        self._docker_repository_name = self.env_name()
        print("docker_repository_name", self._docker_repository_name)
        luigi_utils.clean(self._docker_repository_name)

    def tearDown(self):
        luigi_utils.clean(self._docker_repository_name)
        self._client.close()

    def setup_luigi_config(self):
        set_docker_repository_config(
            docker_password=None,
            docker_repository_name=self._docker_repository_name,
            docker_username=None,
            tag_prefix="",
            kind="target"
        )

    def run_spawn_test_env(self):
        self.setup_luigi_config()
        luigi_utils.set_job_id(SpawnTestEnvironment)
        task = SpawnTestEnvironment(reuse_database_setup=True,
                                    reuse_database=True,
                                    reuse_test_container=True,
                                    external_exasol_xmlrpc_host="",
                                    external_exasol_db_host="",
                                    external_exasol_xmlrpc_port=0,
                                    external_exasol_db_user="",
                                    no_test_container_cleanup_after_success=True,
                                    no_database_cleanup_after_success=True,
                                    external_exasol_db_password="",
                                    external_exasol_xmlrpc_user="",
                                    external_exasol_xmlrpc_password="",
                                    external_exasol_xmlrpc_cluster_name="",
                                    external_exasol_bucketfs_write_password="",
                                    environment_type=EnvironmentType.docker_db,
                                    environment_name=self.env_name(),
                                    docker_db_image_version="7.1.1",
                                    docker_db_image_name="exasol/docker-db"
                                    )
        try:
            success = luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
            if success:
                result = task.get_return_object()
                task.cleanup(True)
                return result
            else:
                task.cleanup(False)
                Exception("Task failed")
        except Exception as e:
            task.cleanup(False)

    def test_initial_reuse_database_setup_populates_data(self):
        username = SpawnTestEnvironment.DEFAULT_DB_USER
        password = SpawnTestEnvironment.DEFAULT_DATABASE_PASSWORD
        test_environment_info = process_spawn_utils.run_in_process(self.run_spawn_test_env)
        test_container = self._client.containers.get(test_environment_info.test_container_info.container_name)
        database_host = test_environment_info.database_info.host
        database_port = test_environment_info.database_info.db_port
        q = "SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA='TEST';"
        cmd = f"""$EXAPLUS -c '{database_host}:{database_port}' -u '{username}' -p '{password}' -sql \\\"{q}\\\""""
        bash_cmd = f"""bash -c "{cmd}" """
        exit_code, output = test_container.exec_run(cmd=bash_cmd)
        output_str = output.decode('utf-8')

        # TODO read /tests/test/import.sql and apply a regular expression to
        # get all table names and compare then one-by-one
        self.assertIn("ENGINETABLE", [output_entry.strip() for output_entry in output_str.split(sep='\n')])
        test_container.remove(force=True)
        self._client.containers\
            .get(test_environment_info.database_info.container_info.container_name).remove(force=True)
        self._client.networks.get(test_environment_info.network_info.network_name).remove()
        self._client.volumes.get(test_environment_info.database_info.container_info.volume_name).remove()

if __name__ == '__main__':
    unittest.main()
