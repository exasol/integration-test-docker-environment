from exasol_integration_test_docker_environment.lib.base.info import Info
from exasol_integration_test_docker_environment.lib.models.data.container_info import (
    ContainerInfo,
)
from exasol_integration_test_docker_environment.lib.models.data.ssh_info import SshInfo
from exasol_integration_test_docker_environment.lib.test_environment.ports import Ports


class DatabaseInfo(Info):
    def __init__(
        self,
        host: str,
        ports: Ports,
        reused: bool,
        container_info: ContainerInfo | None = None,
        ssh_info: SshInfo | None = None,
        forwarded_ports: Ports | None = None,
    ) -> None:
        self.container_info = container_info
        self.ports = ports
        self.host = host
        self.reused = reused
        self.ssh_info = ssh_info
        self.forwarded_ports = forwarded_ports
