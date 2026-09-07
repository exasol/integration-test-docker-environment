"""Shared API-to-task conversion for optional port-forwarding settings."""


def confd_port_forwarding_parameters(
    confd_port_forward: int | None,
    port_bind_address: str | None,
) -> dict[str, str | None]:
    """Return task parameters for the optional ConfD port forwarding."""
    return {
        "confd_port_forward": (
            str(confd_port_forward) if confd_port_forward is not None else None
        ),
        "port_bind_address": port_bind_address,
    }
