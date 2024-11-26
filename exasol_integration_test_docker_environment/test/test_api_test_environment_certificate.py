import unittest

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.test_environment.db_version import (
    db_version_supports_custom_certificates,
)
from exasol_integration_test_docker_environment.test.get_test_container_content import (
    get_test_container_content,
)
from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing.api_test_environment import (
    ApiTestEnvironment,
)
from exasol_integration_test_docker_environment.testing.utils import (
    check_db_version_from_env,
)


class CertificateTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print(f"SetUp {cls.__name__}")
        cls.test_environment = ApiTestEnvironment(cls)

        cls.spawned_docker_test_environments = None

        if db_version_supports_custom_certificates(check_db_version_from_env()):
            # Important: The test environment will create a hostname consisting of a prefix + the class name +
            #            the docker environment in the following parameter
            #            However, host name length is limited to 63 characters. A the class name itself already creates
            #            a unique environment, we must keep the parameter empty.
            cls.docker_environment_name = ""
            additional_parameter = {"create_certificates": True}

            cls.on_host_docker_environment = (
                cls.test_environment.spawn_docker_test_environment_with_test_container(
                    cls.docker_environment_name,
                    test_container_content=get_test_container_content(),
                    additional_parameter=additional_parameter,
                )
            )

    @classmethod
    def tearDownClass(cls):
        utils.close_environments(
            cls.spawned_docker_test_environments, cls.test_environment
        )

    @unittest.skipIf(
        not db_version_supports_custom_certificates(check_db_version_from_env()),
        "Database not supported",
    )
    def test_certificate(self):
        with ContextDockerClient() as docker_client:
            test_container_name = (
                self.on_host_docker_environment.environment_info.test_container_info.container_name
            )
            test_container = docker_client.containers.get(test_container_name)
            database_container = (
                self.on_host_docker_environment.environment_info.database_info.container_info.container_name
            )
            database_network_name = (
                self.on_host_docker_environment.environment_info.database_info.container_info.network_info.network_name
            )
            db_port = (
                self.on_host_docker_environment.environment_info.database_info.ports.database
            )

            openssl_check_cmd = f"openssl s_client -connect {database_container}.{database_network_name}:{db_port}"
            print(f"OpenSSL cmd:{openssl_check_cmd}")
            exit_code, output = test_container.exec_run(openssl_check_cmd)
            print(f"fOpenSSL out:{output}")
            self.assertEqual(exit_code, 0)
            log = output.decode("utf-8")
            expected_subject = (
                f"subject=C = XX, ST = N/A, L = N/A, O = Self-signed certificate, "
                f"CN = {database_container}"
            )
            self.assertIn(expected_subject, log, "Certificate check")


if __name__ == "__main__":
    unittest.main()
