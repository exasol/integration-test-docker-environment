from exasol_integration_test_docker_environment.lib.base.info import Info
from exasol_integration_test_docker_environment.lib.models.data.confd_info import (
    ConfdInfo,
)
from exasol_integration_test_docker_environment.lib.models.data.container_info import (
    ContainerInfo,
)
from exasol_integration_test_docker_environment.lib.models.data.published_port import (
    PublishedPort,
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
        port_bind_address: str | None = None,
        confd_info: ConfdInfo | None = None,
        published_ports: dict[str, PublishedPort] | None = None,
    ) -> None:
        self.container_info = container_info
        self.ports = ports
        self.host = host
        self.reused = reused
        self.ssh_info = ssh_info
        self.forwarded_ports = forwarded_ports
        self.port_bind_address = port_bind_address
        # The former fields are retained as compatibility metadata. New
        # clients use this mapping so they never reconstruct a publication.
        self.published_ports = (
            self._published_ports(ports, forwarded_ports, port_bind_address)
            if published_ports is None
            else published_ports
        )
        self.confd_info = confd_info

    @staticmethod
    def _published_ports(
        container_ports: Ports,
        forwarded_ports: Ports | None,
        bind_address: str | None,
    ) -> dict[str, PublishedPort]:
        if forwarded_ports is None:
            return {}
        return {
            name: PublishedPort(container_port, host_port, bind_address or "127.0.0.1")
            for name, container_port, host_port in (
                ("database", container_ports.database, forwarded_ports.database),
                (
                    "bucketfs_http",
                    container_ports.bucketfs_http,
                    forwarded_ports.bucketfs_http,
                ),
                ("ssh", container_ports.ssh, forwarded_ports.ssh),
                (
                    "bucketfs_https",
                    container_ports.bucketfs_https,
                    forwarded_ports.bucketfs_https,
                ),
                ("confd", container_ports.confd, forwarded_ports.confd),
            )
            if container_port is not None and host_port is not None
        }

    def published_port(self, name: str) -> PublishedPort | None:
        # Existing reusable environments can have been serialized before the
        # mapping was introduced.
        published_ports = getattr(self, "published_ports", None)
        if published_ports is None:
            published_ports = self._published_ports(
                self.ports, self.forwarded_ports, self.port_bind_address
            )
        return published_ports.get(name)
