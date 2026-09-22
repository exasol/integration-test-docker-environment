"""ITDE coverage for the opt-in, local ConfD JSON-RPC boundary."""

import base64
import ssl
from pathlib import Path
from urllib.request import (
    Request,
    urlopen,
)

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.test_environment.ports import (
    find_free_ports,
)


def test_confd_port_defaults_to_loopback(api_context):
    """ConfD remains local when no bind address is explicitly configured."""
    confd_port = find_free_ports(1)[0]
    with api_context(
        additional_parameters={"confd_port_forward": confd_port},
    ) as environment:
        container_info = environment.environment_info.database_info.container_info
        assert container_info is not None
        with ContextDockerClient() as docker_client:
            container = docker_client.containers.get(container_info.container_name)
            container.reload()
        bindings = container.attrs["NetworkSettings"]["Ports"]
        assert bindings["443/tcp"] == [
            {"HostIp": "127.0.0.1", "HostPort": str(confd_port)}
        ]


def test_port_bind_address_applies_to_confd_and_database(api_context):
    """Docker applies the requested bind address to every forwarded port."""
    confd_port = find_free_ports(1)[0]
    with api_context(
        additional_parameters={
            "confd_port_forward": confd_port,
            "port_bind_address": "127.0.0.1",
        },
    ) as environment:
        environment_info = environment.environment_info
        database_info = environment_info.database_info
        container_info = database_info.container_info
        assert container_info is not None
        assert database_info.forwarded_ports is not None
        database_port = database_info.forwarded_ports.database
        assert database_info.forwarded_ports.confd == confd_port
        with ContextDockerClient() as docker_client:
            container = docker_client.containers.get(container_info.container_name)
            container.reload()
        bindings = container.attrs["NetworkSettings"]["Ports"]
        assert bindings["8563/tcp"] == [
            {"HostIp": "127.0.0.1", "HostPort": str(database_port)}
        ]
        assert bindings["443/tcp"] == [
            {"HostIp": "127.0.0.1", "HostPort": str(confd_port)}
        ]


def test_confd_credentials_authenticate_at_the_forwarded_endpoint(api_context):
    """ITDE exposes a credential contract without serializing its password."""
    confd_port = find_free_ports(1)[0]
    credentials_file = None
    with api_context(
        additional_parameters={
            "confd_port_forward": confd_port,
            "create_confd_user": True,
        },
    ) as environment:
        environment_info = environment.environment_info
        database_info = environment_info.database_info
        confd_info = database_info.confd_info
        assert confd_info is not None
        assert confd_info.endpoint == f"https://127.0.0.1:{confd_port}/RPC2"
        assert confd_info.tunnel_target_host == database_info.host
        assert confd_info.tunnel_target_port == 443
        credentials_file = Path(confd_info.credentials_file)
        assert credentials_file.stat().st_mode & 0o077 == 0

        credentials = confd_info.read_credentials()
        assert credentials.password not in environment_info.to_json()
        request = Request(
            confd_info.endpoint,
            data=(
                b'<?xml version="1.0"?><methodCall>'
                b"<methodName>system.listMethods</methodName><params/></methodCall>"
            ),
            headers={
                "Authorization": "Basic "
                + base64.b64encode(
                    f"{credentials.username}:{credentials.password}".encode()
                ).decode(),
                "Content-Type": "text/xml",
            },
            method="POST",
        )
        with urlopen(
            request, context=ssl._create_unverified_context(), timeout=10
        ) as response:  # noqa: SLF001
            assert response.status == 200
            assert b"methodResponse" in response.read()

    assert credentials_file is not None
    assert not credentials_file.exists()
