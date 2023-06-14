from exasol_integration_test_docker_environment.lib.base.ssh_access import SshKey

class SshInfo:
    """
    key_file contains path to the file containing the private key for SSH access.
    """
    def __init__(self, user: str, port: int, key_file: str):
        self.user = user
        self.port = port
        self.key_file = key_file
