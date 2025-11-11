import logging
import socket
from collections.abc import Generator
from contextlib import ExitStack
from typing import (
    Optional,
)


def find_free_ports(num_ports: int) -> list[int]:
    def new_socket():
        return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def bind(sock: socket.socket, port: int):
        sock.bind(("", port))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def acquire_port_numbers(num_ports: int) -> Generator[int, None, None]:
        with ExitStack() as stack:
            sockets = [stack.enter_context(new_socket()) for dummy in range(num_ports)]
            for sock in sockets:
                bind(sock, 0)
                yield sock.getsockname()[1]

    def check_port_numbers(ports):
        with ExitStack() as stack:
            sockets_and_ports = [
                (stack.enter_context(new_socket()), port) for port in ports
            ]
            for sock, port in sockets_and_ports:
                bind(sock, port)

    ports = list(acquire_port_numbers(num_ports))
    check_port_numbers(ports)
    return ports


class PortsType(type):
    """
    The following properties are read-only class attributes:
    - default_ports
    - external
    - forward
    """

    @property
    def default_ports(self) -> "Ports":
        return Ports(database=8563, bucketfs=2580, ssh=22, bucketfs_https=2581)

    @property
    def external(self) -> "Ports":
        # For external databases SSH port might depend on version database.
        return Ports(database=8563, bucketfs=2580, ssh=None, bucketfs_https=2581)

    @property
    def forward(self) -> "Ports":
        return Ports(database=8563, bucketfs=2580, ssh=20002, bucketfs_https=2581)


class Ports(metaclass=PortsType):
    def __init__(
        self,
        database: Optional[int],
        bucketfs: Optional[int],
        ssh: Optional[int] = None,
        bucketfs_https: Optional[int] = None,
    ) -> None:
        if database is None:
            self._database: int = Ports.default_ports.database
        else:
            self._database = database
        if bucketfs is None:
            self._bucketfs_http: int = Ports.default_ports.bucketfs_http
        else:
            self._bucketfs_http = bucketfs
        self._ssh = ssh
        if bucketfs_https is None:
            self._bucketfs_https: int = Ports.default_ports.bucketfs_https
        else:
            self._bucketfs_https = bucketfs_https

    @property
    def bucketfs(self) -> int:
        logging.warn(
            f"Property Ports.bucketfs is deprecated, use Ports.bucketfs_http instead.",
            DeprecationWarning,
        )
        return self._bucketfs_https

    @bucketfs.setter
    def bucketfs(self, value: int) -> None:
        logging.warn(
            f"Property Ports.bucketfs is deprecated, use Ports.bucketfs_http instead.",
            DeprecationWarning,
        )
        self._bucketfs_https = value

    @property
    def bucketfs_http(self) -> int:
        return self._bucketfs_http

    @bucketfs_http.setter
    def bucketfs_http(self, value: int) -> None:
        logging.warn(
            f"Setting values of class Ports after instantiation is deprecated.",
            DeprecationWarning,
        )
        self._bucketfs_http = value

    @property
    def bucketfs_https(self) -> int:
        return self._bucketfs_https

    @bucketfs_https.setter
    def bucketfs_https(self, value: int) -> None:
        logging.warn(
            f"Setting values of class Ports after instantiation is deprecated.",
            DeprecationWarning,
        )
        self._bucketfs_https = value

    @property
    def database(self) -> int:
        return self._database

    @database.setter
    def database(self, value: int) -> None:
        logging.warn(
            f"Setting values of class Ports after instantiation is deprecated.",
            DeprecationWarning,
        )
        self._database = value

    @property
    def ssh(self) -> Optional[int]:
        return self._ssh

    @ssh.setter
    def ssh(self, value: Optional[int]) -> None:
        logging.warn(
            f"Setting values of class Ports after instantiation is deprecated.",
            DeprecationWarning,
        )
        self._ssh = value

    @classmethod
    def random_free(cls, ssh: bool = True) -> "Ports":
        count = 4 if ssh else 3
        ports = find_free_ports(count)
        return (
            Ports(ports[0], ports[1], None, ports[2])
            if not ssh
            else Ports(ports[0], ports[1], ports[2], ports[3])
        )
