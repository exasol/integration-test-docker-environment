from typing import Optional

from exasol_integration_test_docker_environment.lib.base.info import Info
from exasol_integration_test_docker_environment.lib.data.container_info import (
    ContainerInfo,
)
from exasol_integration_test_docker_environment.lib.data.ssh_info import SshInfo
from exasol_integration_test_docker_environment.lib.test_environment.ports import Ports


class DatabaseInfo(Info):
    def __init__(
        self,
        host: str,
        ports: Ports,
        reused: bool,
        container_info: Optional[ContainerInfo] = None,
        ssh_info: Optional[SshInfo] = None,
        forwarded_ports: Optional[Ports] = None,
    ):
        self.container_info = container_info
        self.ports = ports
        self.host = host
        self.reused = reused
        self.ssh_info = ssh_info
        self.forwarded_ports = forwarded_ports
