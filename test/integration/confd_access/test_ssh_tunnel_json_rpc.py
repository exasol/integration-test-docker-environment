"""SSH-tunneled ConfD JSON-RPC integration scenarios."""

from test.integration.confd_access.json_rpc import (
    assert_db_list_response,
    authentication_token_db_list_request,
    basic_db_list_request,
)


def test_ssh_tunnel_json_rpc_basic(confd_ssh_tunnel_json_rpc_access, fabric_stdin):
    """The SSH tunnel reaches the internal HTTPS endpoint with Basic auth."""
    assert_db_list_response(
        basic_db_list_request(
            confd_ssh_tunnel_json_rpc_access.endpoint,
            confd_ssh_tunnel_json_rpc_access.username,
            confd_ssh_tunnel_json_rpc_access.password,
        )
    )


def test_ssh_tunnel_json_rpc_token(confd_ssh_tunnel_json_rpc_access, fabric_stdin):
    """The SSH-tunnel route accepts the EXAConf authentication token."""
    assert_db_list_response(
        authentication_token_db_list_request(
            confd_ssh_tunnel_json_rpc_access.endpoint,
            confd_ssh_tunnel_json_rpc_access.token,
        )
    )
