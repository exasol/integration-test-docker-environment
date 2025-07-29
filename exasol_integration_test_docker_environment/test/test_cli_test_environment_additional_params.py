import unittest

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing.exaslct_test_environment import (
    ExaslctTestEnvironment,
)

ADDITIONAL_DB_PARAMS = ["-disableIndexIteratorScan=1", "-disableIndexIteratorScan=1"]


class DockerTestEnvironmentAdditionParamsTest(unittest.TestCase):
    """
    Deprecated. Replaced by "./test/integration/test_api_test_environment_additional_params.py"
    """

    @classmethod
    def setUpClass(cls):
        print(f"SetUp {cls.__name__}")
        cls.test_environment = ExaslctTestEnvironment(
            cls,
            utils.INTEGRATION_TEST_DOCKER_ENVIRONMENT_DEFAULT_BIN,
            clean_images_at_close=False,
        )
        # TODO cls.test_environment.clean_images()
        cls.docker_environment_name = cls.__name__
        additional_db_parameters = [
            f"--additional-db-parameter {add_param}"
            for add_param in ADDITIONAL_DB_PARAMS
        ]
        cls.spawned_docker_test_environments = (
            cls.test_environment.spawn_docker_test_environments(
                name=cls.docker_environment_name,
                additional_parameter=additional_db_parameters,
            )
        )

    @classmethod
    def tearDownClass(cls):
        utils.close_environments(
            cls.spawned_docker_test_environments, cls.test_environment
        )

    def test_additional_params_are_used(self):
        environment_info = (
            self.spawned_docker_test_environments.on_host_docker_environment
        )
        db_container_name = (
            environment_info.environment_info.database_info.container_info.container_name
        )
        with ContextDockerClient() as docker_client:
            db_container = docker_client.containers.get(db_container_name)
            exit_code, output = db_container.exec_run("dwad_client print-params DB1")
            self.assertEqual(
                exit_code,
                0,
                f"Error while executing 'dwad_client' "
                f"in db container got output\n {output.decode('UTF-8')}.",
            )
            params_lines = [
                line
                for line in output.decode("UTF-8").splitlines()
                if line.startswith("Parameters:")
            ]
            self.assertEqual(
                len(params_lines), 1, "Unexpected format of output of dwad_client"
            )
            params_line = params_lines[0]
            for add_db_param in ADDITIONAL_DB_PARAMS:
                self.assertIn(add_db_param, params_line)


if __name__ == "__main__":
    unittest.main()
