from typing import (
    Optional,
)

from exasol_integration_test_docker_environment.lib.base.info import Info
from exasol_integration_test_docker_environment.lib.models.data.docker_network_info import (
    DockerNetworkInfo,
)


class ContainerInfo(Info):

    def __init__(
        self,
        container_name: str,
        ip_address: str,
        network_aliases: list[str],
        network_info: DockerNetworkInfo,
        volume_name: Optional[str] = None,
    ) -> None:
        self.network_aliases = network_aliases
        self.ip_address = ip_address
        self.network_info = network_info
        self.container_name = container_name
        self.volume_name = volume_name
