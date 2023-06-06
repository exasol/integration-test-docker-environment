from exasol_integration_test_docker_environment.lib.base.info import Info
from exasol_integration_test_docker_environment.lib.data.container_info import ContainerInfo
from exasol_integration_test_docker_environment.lib.test_environment.ports import PortForwarding


class DatabaseInfo(Info):
    def __init__(self, host: str, ports: PortForwarding,
                 reused: bool, container_info: ContainerInfo = None):
        self.container_info = container_info
        self.ports = ports
        self.host = host
        self.reused = reused
