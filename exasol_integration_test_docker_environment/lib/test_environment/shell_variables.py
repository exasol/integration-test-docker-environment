from typing import (
    Dict,
    Optional,
)

from exasol_integration_test_docker_environment.lib.data.environment_info import (
    EnvironmentInfo,
)


class ShellVariables:
    """
    Represents a collection of unix shell environment variables.
    """

    def __init__(self, env: Dict[str, str]):
        self.env = env

    @classmethod
    def from_test_environment_info(
        cls,
        default_bridge_ip_address: Optional[str],
        test_environment_info: EnvironmentInfo,
    ) -> "ShellVariables":
        """
        Create ShellVariables from the given test_container_name,
        default_bridge_ip_address and EnvironmentInfo.
        """
        info = test_environment_info
        assert info.database_info.ports.database is not None
        assert info.database_info.ports.bucketfs is not None
        env: Dict[str, str] = {
            "NAME": info.name,
            "TYPE": info.type if isinstance(info.type, str) else info.type.name,
            "DATABASE_HOST": info.database_info.host,
            "DATABASE_DB_PORT": str(info.database_info.ports.database),
            "DATABASE_BUCKETFS_PORT": str(info.database_info.ports.bucketfs),
            "DATABASE_SSH_PORT": (
                str(info.database_info.ports.ssh)
                if info.database_info.ports.ssh is not None
                else ""
            ),
        }

        if info.database_info.container_info is not None:
            assert info.database_info.container_info.volume_name
            assert default_bridge_ip_address
            network_aliases = " ".join(
                info.database_info.container_info.network_aliases
            )
            env.update(
                {
                    "DATABASE_CONTAINER_NAME": info.database_info.container_info.container_name,
                    "DATABASE_CONTAINER_NETWORK_ALIASES": f'"{network_aliases}"',
                    "DATABASE_CONTAINER_IP_ADDRESS": info.database_info.container_info.ip_address,
                    "DATABASE_CONTAINER_VOLUMNE_NAME": info.database_info.container_info.volume_name,
                    "DATABASE_CONTAINER_DEFAULT_BRIDGE_IP_ADDRESS": default_bridge_ip_address,
                }
            )
        if info.test_container_info is not None:
            container_name = info.test_container_info.container_name
            network_aliases = " ".join(info.test_container_info.network_aliases)
            env.update(
                {
                    "TEST_CONTAINER_NAME": container_name,
                    "TEST_CONTAINER_NETWORK_ALIASES": f'"{network_aliases}"',
                    "TEST_CONTAINER_IP_ADDRESS": info.test_container_info.ip_address,
                }
            )
        return ShellVariables(env)

    def render(self, prefix: str = "") -> str:
        prefix += "ITDE"
        aslist = [f"{prefix}_{key}={value}" for key, value in self.env.items()]
        return "\n".join(aslist) + "\n"
