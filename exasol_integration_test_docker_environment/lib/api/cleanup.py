from pathlib import Path

from exasol_integration_test_docker_environment.lib.docker.container.utils import (
    remove_docker_container,
)
from exasol_integration_test_docker_environment.lib.docker.networks.utils import (
    remove_docker_networks,
)
from exasol_integration_test_docker_environment.lib.docker.volumes.utils import (
    remove_docker_volumes,
)
from exasol_integration_test_docker_environment.lib.models.data.environment_info import (
    EnvironmentInfo,
)


def cleanup_test_environment(environment_info: EnvironmentInfo) -> None:
    """Remove test-environment resources and its disposable ConfD credentials."""
    confd_info = environment_info.database_info.confd_info
    try:
        if test_container_info := environment_info.test_container_info:
            remove_docker_container([test_container_info.container_name])

        if db_container_info := environment_info.database_info.container_info:
            remove_docker_container([db_container_info.container_name])
            if volume_name := db_container_info.volume_name:
                remove_docker_volumes([volume_name])

        remove_docker_networks([environment_info.network_info.network_name])
    finally:
        if confd_info is not None:
            Path(confd_info.credentials_file).unlink(missing_ok=True)
