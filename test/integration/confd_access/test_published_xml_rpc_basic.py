"""Published ConfD XML-RPC Basic-auth integration scenario."""

import base64
import ssl
from pathlib import Path
from urllib.request import (
    Request,
    urlopen,
)

from exasol_integration_test_docker_environment.lib.test_environment.ports import (
    find_free_ports,
)


def test_published_xml_rpc_basic(api_context):
    """ITDE credentials authenticate at the published XML-RPC endpoint."""
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
