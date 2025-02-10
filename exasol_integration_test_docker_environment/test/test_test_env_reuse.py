import unittest

import luigi

from exasol_integration_test_docker_environment.cli.options import (
    test_environment_options,
)
from exasol_integration_test_docker_environment.lib.api.run_task import (
    generate_root_task,
)
from exasol_integration_test_docker_environment.lib.config.docker_config import (
    set_docker_repository_config,
)
from exasol_integration_test_docker_environment.lib.data.environment_type import (
    EnvironmentType,
)
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.test_environment.ports import Ports
from exasol_integration_test_docker_environment.lib.test_environment.spawn_test_environment import (
    SpawnTestEnvironment,
)
from exasol_integration_test_docker_environment.test.get_test_container_content import (
    get_test_container_content,
)
from exasol_integration_test_docker_environment.testing import luigi_utils
from exasol_integration_test_docker_environment.testing.utils import (
    check_db_version_from_env,
)


class TestContainerReuseTest(unittest.TestCase):
    """
    This test spawns a new test environment and, with parameters:
    * reuse_database_setup=True,
    * reuse_database=True,
    * reuse_test_container=True
    and verifies if the test data was populated to the docker db.
    """

    def env_name(self):
        return self.__class__.__name__.lower()

    def setUp(self):
        self._docker_repository_name = self.env_name()
        print("docker_repository_name", self._docker_repository_name)
        luigi_utils.clean(self._docker_repository_name)

        self.docker_db_version_parameter = (
            check_db_version_from_env() or test_environment_options.LATEST_DB_VERSION
        )

        self.setup_luigi_config()
        self.ports = Ports.random_free()

    def tearDown(self):
        luigi_utils.clean(self._docker_repository_name)

    def setup_luigi_config(self):
        set_docker_repository_config(
            docker_password=None,
            docker_repository_name=self._docker_repository_name,
            docker_username=None,
            tag_prefix="",
            kind="target",
        )

    def run_spawn_test_env(self, cleanup: bool):
        result = None
        task = generate_root_task(
            task_class=SpawnTestEnvironment,
            reuse_database_setup=True,
            reuse_database=True,
            reuse_test_container=True,
            no_test_container_cleanup_after_success=not cleanup,
            no_database_cleanup_after_success=not cleanup,
            external_exasol_db_port=self.ports.database,
            external_exasol_bucketfs_port=self.ports.bucketfs,
            external_exasol_ssh_port=self.ports.ssh,
            external_exasol_xmlrpc_host="",
            external_exasol_db_host="",
            external_exasol_xmlrpc_port=0,
            external_exasol_db_user="",
            external_exasol_db_password="",
            external_exasol_xmlrpc_user="",
            external_exasol_xmlrpc_password="",
            external_exasol_xmlrpc_cluster_name="",
            external_exasol_bucketfs_write_password="",
            environment_type=EnvironmentType.docker_db,
            environment_name=self.env_name(),
            docker_db_image_version=self.docker_db_version_parameter,
            docker_db_image_name="exasol/docker-db",
            test_container_content=get_test_container_content(),
            additional_db_parameter=tuple(),
        )
        try:
            success = luigi.build(
                [task], workers=1, local_scheduler=True, log_level="INFO"
            )
            if success:
                result = task
            else:
                raise Exception("Task failed")
        except Exception as e:
            task.cleanup(False)
            raise RuntimeError("Error spawning test environment") from e
        return result

    def _create_exaplus_check_cmd(self, test_environment_info):
        username = SpawnTestEnvironment.DEFAULT_DB_USER
        password = SpawnTestEnvironment.DEFAULT_DATABASE_PASSWORD
        database_host = test_environment_info.database_info.host
        database_port = test_environment_info.database_info.db_port
        q = "SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA='TEST';"
        return (
            f"$EXAPLUS -c '{database_host}:{database_port}' -u '{username}' -p '{password}' "
            f"-jdbcparam 'validateservercertificate=0' -sql \\\"{q}\\\""
        )

    def _exec_cmd_in_test_container(self, test_environment_info, cmd):
        with ContextDockerClient() as docker_client:
            bash_cmd = f"""bash -c "{cmd}" """
            test_container = docker_client.containers.get(
                test_environment_info.test_container_info.container_name
            )

            exit_code, output = test_container.exec_run(cmd=bash_cmd)
            self.assertEqual(exit_code, 0)
            return output.decode("utf-8")

    def get_instance_ids(self, test_environment_info):
        with ContextDockerClient() as docker_client:
            test_container = docker_client.containers.get(
                test_environment_info.test_container_info.container_name
            )
            db_container = docker_client.containers.get(
                test_environment_info.database_info.container_info.container_name
            )
            network = docker_client.networks.get(
                test_environment_info.network_info.network_name
            )
            return test_container.id, db_container.id, network.id

    def test_reuse_env_same_instances(self):
        task = self.run_spawn_test_env(cleanup=False)
        test_environment_info = task.get_result()
        old_instance_ids = self.get_instance_ids(test_environment_info)
        # This clean is supposed to not remove docker instances
        task.cleanup(True)

        task = self.run_spawn_test_env(cleanup=True)
        test_environment_info = task.get_result()
        new_instance_ids = self.get_instance_ids(test_environment_info)
        self.assertEqual(old_instance_ids, new_instance_ids)

        task.cleanup(True)


if __name__ == "__main__":
    unittest.main()
