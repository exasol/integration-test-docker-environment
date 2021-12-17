import unittest


from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.test_environment import db_version_supports_custom_certificates
from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing.exaslct_test_environment import ExaslctTestEnvironment
from exasol_integration_test_docker_environment.testing.utils import check_db_version_from_env


class CertificateTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print(f"SetUp {cls.__name__}")
        # We can't use start-test-env. because it only mounts ./ and
        # doesn't work with --build_ouput-directory
        cls.test_environment = \
            ExaslctTestEnvironment(
                cls,
                utils.INTEGRATION_TEST_DOCKER_ENVIRONMENT_DEFAULT_BIN,
                clean_images_at_close=False)

        cls.spawned_docker_test_environments = None

        if db_version_supports_custom_certificates(check_db_version_from_env()):
            # Important: The test environment will create a hostname consisting of a prefix + the class name +
            #            the docker environment in the following parameter
            #            However, host name length is limited to 63 characters. A the class name itself already creates
            #            a unique environment, we must keep the parameter empty.
            cls.docker_environment_name = ""
            cls.spawned_docker_test_environments = \
                cls.test_environment.spawn_docker_test_environments(cls.docker_environment_name,
                                                                    additional_parameter=["--deactivate-database-setup",
                                                                                          "--create-certificates"])

    @classmethod
    def tearDownClass(cls):
        utils.close_environments(cls.spawned_docker_test_environments, cls.test_environment)

    @unittest.skipIf(not db_version_supports_custom_certificates(check_db_version_from_env()), "Database not supported")
    def test_certificate(self):
        on_host_docker_environment = self.spawned_docker_test_environments.on_host_docker_environment
        with ContextDockerClient() as docker_client:
            test_container = docker_client.containers.get(f"test_container_{on_host_docker_environment.name}")

            host_name = f"{on_host_docker_environment.environment_info.database_info.container_info.container_name}." \
                        f"{on_host_docker_environment.environment_info.network_info.network_name}"
            db_port = f"{on_host_docker_environment.environment_info.database_info.db_port}"
            openssl_check_cmd = f"openssl s_client -connect {host_name}:{db_port}"
            print(f"OpenSSL cmd:{openssl_check_cmd}")
            exit_code, output = test_container.exec_run(openssl_check_cmd)
            print(f"fOpenSSL out:{output}")
            self.assertEqual(exit_code, 0)
            log = output.decode("utf-8")
            expected_subject = f"subject=C = XX, ST = N/A, L = N/A, O = Self-signed certificate, " \
                               f"CN = {host_name}"
            self.assertIn(expected_subject, log, "Certificate check")


if __name__ == '__main__':
    unittest.main()
