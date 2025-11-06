import unittest
from sys import stderr

from exasol_integration_test_docker_environment.lib.base.run_task import (
    generate_root_task,
    run_task,
)
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.docker.container.utils import (
    remove_docker_container,
)
from exasol_integration_test_docker_environment.lib.models.data.environment_info import (
    EnvironmentInfo,
)
from exasol_integration_test_docker_environment.lib.models.data.environment_type import (
    EnvironmentType,
)
from exasol_integration_test_docker_environment.lib.test_environment.spawn_test_environment import (
    SpawnTestEnvironment,
)
from exasol_integration_test_docker_environment.test.get_test_container_content import (
    get_test_container_content,
)
from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing.api_test_environment import (
    ApiTestEnvironment,
)


class APISpawnTestExternalEnvironmentTest(unittest.TestCase):
    """
    Deprecated. Replaced by "./test/integration/test_api_external_test_environment.py"
    """

    @classmethod
    def setUpClass(cls):
        print(f"SetUp {cls.__name__}", file=stderr)
        cls.test_environment = ApiTestEnvironment(cls)
        cls.docker_environment_name = cls.__name__
        cls.environment = cls.test_environment.spawn_docker_test_environment(
            name=cls.docker_environment_name
        )
        cls.ext_environment_name = "APISpawnExternalTestExternalEnvironmentTest"

        task_creator = lambda: generate_root_task(
            task_class=SpawnTestEnvironment,
            environment_type=EnvironmentType.external_db,
            environment_name=cls.ext_environment_name,
            external_exasol_db_host=cls.environment.database_host,
            external_exasol_db_port=cls.environment.ports.database,
            external_exasol_bucketfs_http_port=cls.environment.ports.bucketfs.http,
            external_exasol_bucketfs_https_port=cls.environment.ports.bucketfs.https,
            external_exasol_ssh_port=cls.environment.ports.ssh,
            external_exasol_db_user=cls.environment.db_username,
            external_exasol_db_password=cls.environment.db_password,
            external_exasol_bucketfs_write_password=cls.environment.bucketfs_password,
            external_exasol_xmlrpc_host=None,
            external_exasol_xmlrpc_port=443,
            external_exasol_xmlrpc_user="admin",
            external_exasol_xmlrpc_password=None,
            external_exasol_xmlrpc_cluster_name="cluster1",
            no_test_container_cleanup_after_success=True,
            no_test_container_cleanup_after_failure=False,
            reuse_test_container=True,
            test_container_content=get_test_container_content(),
            additional_db_parameter=(),
            docker_environment_variables=(),
            accelerator=(),
        )
        cls.ext_environment_info: EnvironmentInfo = run_task(task_creator, 1, None)

    @classmethod
    def tearDownClass(cls):
        utils.close_environments(cls.environment, cls.test_environment)
        with ContextDockerClient() as docker_client:
            containers = [
                c.name
                for c in docker_client.containers.list()
                if cls.ext_environment_name in c.name
            ]
            remove_docker_container(containers)

    def test_external_db(self):
        with ContextDockerClient() as docker_client:
            containers = [
                c.name
                for c in docker_client.containers.list()
                if self.docker_environment_name in c.name
            ]
            self.assertEqual(
                len(containers), 1, f"Not exactly 1 containers in {containers}."
            )
            db_container = [c for c in containers if "db_container" in c]
            self.assertEqual(
                len(db_container), 1, f"Found no db container in {containers}."
            )
            containers = [
                c.name
                for c in docker_client.containers.list()
                if self.ext_environment_name in c.name
            ]
            self.assertEqual(
                len(containers), 1, f"Not exactly 1 containers in {containers}."
            )
            test_container = [c for c in containers if "test_container" in c]
            self.assertEqual(
                len(test_container), 1, f"Found no test container in {containers}."
            )

    def test_docker_available_in_test_container(self):
        environment_info = self.ext_environment_info
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


if __name__ == "__main__":
    unittest.main()
