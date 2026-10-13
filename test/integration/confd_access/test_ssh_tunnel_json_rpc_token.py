"""SSH-tunneled ConfD JSON-RPC authentication-token integration scenario."""

from test.integration.confd_access.json_rpc import (
    assert_db_list_response,
    authentication_token_db_list_request,
)


def test_ssh_tunnel_json_rpc_token(confd_ssh_tunnel_json_rpc_token_access):
    """The SSH-tunnel route accepts the EXAConf authentication token."""
    with confd_ssh_tunnel_json_rpc_token_access() as access:
        assert_db_list_response(
            authentication_token_db_list_request(access.endpoint, access.token)
        )
