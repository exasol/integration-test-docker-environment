from typing import (
    Optional,
    Union,
)

from exasol_integration_test_docker_environment.lib.base.info import Info
from exasol_integration_test_docker_environment.lib.data.container_info import (
    ContainerInfo,
)
from exasol_integration_test_docker_environment.lib.data.database_info import (
    DatabaseInfo,
)
from exasol_integration_test_docker_environment.lib.data.docker_network_info import (
    DockerNetworkInfo,
)
from exasol_integration_test_docker_environment.lib.data.environment_type import (
    EnvironmentType,
)


class EnvironmentInfo(Info):

    def __init__(
        self,
        name: str,
        env_type: Union[str, EnvironmentType],
        database_info: DatabaseInfo,
        test_container_info: Optional[ContainerInfo],
        network_info: DockerNetworkInfo,
    ):
        self.name = name
        self.type = env_type
        self.test_container_info = test_container_info
        self.database_info = database_info
        self.network_info = network_info
