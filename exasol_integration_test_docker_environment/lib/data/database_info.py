from exasol_integration_test_docker_environment.lib.base.info import Info
from exasol_integration_test_docker_environment.lib.data.container_info import ContainerInfo
from exasol_integration_test_docker_environment.lib.test_environment.ports import Ports
from exasol_integration_test_docker_environment.lib.data.ssh_info import SshInfo


class DatabaseInfo(Info):
    def __init__(
            self,
            host: str,
            ports: Ports,
            reused: bool,
            container_info: ContainerInfo = None,
            ssh_info: SshInfo = None,
            forwarded_ports: Ports = None,
    ):
        self.container_info = container_info
        self.ports = ports
        self.host = host
        self.reused = reused
        self.ssh_info = ssh_info
        self.forwarded_ports = forwarded_ports
