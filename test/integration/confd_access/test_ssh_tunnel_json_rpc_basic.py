"""SSH-tunneled ConfD JSON-RPC Basic-auth integration scenario."""

from test.integration.confd_access.json_rpc import (
    assert_db_list_response,
    basic_db_list_request,
)


def test_ssh_tunnel_json_rpc_basic(confd_ssh_tunnel_json_rpc_basic_access):
    """The SSH tunnel reaches the internal HTTPS endpoint with Basic auth."""
    with confd_ssh_tunnel_json_rpc_basic_access() as access:
        assert_db_list_response(
            basic_db_list_request(access.endpoint, access.username, access.password)
        )
