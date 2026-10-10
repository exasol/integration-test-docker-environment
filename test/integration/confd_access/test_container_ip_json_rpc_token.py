"""Container-IP ConfD JSON-RPC bearer-token integration scenario."""

from test.integration.confd_access.json_rpc import (
    assert_db_list_response,
    bearer_token_db_list_request,
)


def test_container_ip_json_rpc_token(confd_container_ip_json_rpc_token_access):
    """The direct container-IP route accepts the EXAConf bearer token."""
    with confd_container_ip_json_rpc_token_access() as access:
        assert_db_list_response(
            bearer_token_db_list_request(access.endpoint, access.token)
        )
