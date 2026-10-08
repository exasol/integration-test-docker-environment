from dataclasses import dataclass


@dataclass(frozen=True)
class PublishedPort:
    """A Docker port publication and the endpoint a host can use for it."""

    container_port: int
    host_port: int
    bind_address: str = "127.0.0.1"

    def local_endpoint(self) -> tuple[str, int]:
        """Return a connectable endpoint from the Docker host.

        Docker's wildcard bind addresses describe where it listens, not a
        destination a client should dial. Use the corresponding loopback
        address when the client runs on the Docker host.
        """
        host = {"0.0.0.0": "127.0.0.1", "::": "::1"}.get(
            self.bind_address, self.bind_address
        )
        return host, self.host_port
