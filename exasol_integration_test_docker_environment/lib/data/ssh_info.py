from exasol_integration_test_docker_environment.lib.base.ssh_access import SshKey

class SshInfo:
    def __init__(self, user: str, port: int, ssh_key: SshKey):
        self.user = user
        self.port = port
        self.ssh_key = ssh_key
