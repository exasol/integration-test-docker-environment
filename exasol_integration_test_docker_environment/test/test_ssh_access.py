import unittest

from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing \
   .exaslct_test_environment import ExaslctTestEnvironment
from exasol_integration_test_docker_environment.lib.base.ssh_access import SshKey


class DockerTestEnvironmentTest(unittest.TestCase):
    """
    This class tests using SSH to access the file system and commandline of the Exasol Database.

    The Docker Container of older database versions allowed to use
    ``docker_exec`` as well, while newer versions require SSH. The user can
    select the access method with an additional commandline option
    --docker-access-method.

    Currently the SSH access is not implemented fully but the current test
    case will verify that when using SSH access a file with the required
    private key is generated.
    """

    @classmethod
    def setUpClass(cls):
        print(f"SetUp {cls.__name__}")
        cls.environment = ExaslctTestEnvironment(cls, "itde", clean_images_at_close=False)
        cls.docker_environment_name = cls.__name__
        cls.spawned = cls.environment.spawn_docker_test_environments(
            name=cls.docker_environment_name,
            additional_parameter = ["--docker-access-method", "SSH"],
        )

    @classmethod
    def tearDownClass(cls):
        utils.close_environments(cls.spawned, cls.environment)

    def test_generate_ssh_key_file(self):
        file = SshKey.default_folder() / "id_rsa"
        self.assertTrue(file.exists())


if __name__ == '__main__':
    unittest.main()
