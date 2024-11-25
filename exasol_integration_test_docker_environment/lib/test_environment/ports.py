import socket
from contextlib import ExitStack
from typing import (
    Generator,
    List,
    Optional,
)


def find_free_ports(num_ports: int) -> List[int]:
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
        return Ports(database=8563, bucketfs=2580, ssh=22)

    @property
    def external(self) -> "Ports":
        # For external databases SSH port might depend on version database.
        return Ports(database=8563, bucketfs=2580, ssh=None)

    @property
    def forward(self) -> "Ports":
        return Ports(database=8563, bucketfs=2580, ssh=20002)


class Ports(metaclass=PortsType):
    def __init__(self, database: int, bucketfs: int, ssh: Optional[int] = None):
        self.database = database
        self.bucketfs = bucketfs
        self.ssh = ssh

    @classmethod
    def random_free(cls, ssh: bool = True) -> "Ports":
        count = 3 if ssh else 2
        ports = find_free_ports(count)
        return (
            Ports(ports[0], ports[1], None)
            if not ssh
            else Ports(ports[0], ports[1], ports[2])
        )
