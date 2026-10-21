"""Published-port ConfD JSON-RPC integration scenarios."""

from test.integration.confd_access.json_rpc import (
    assert_db_list_response,
    authentication_token_db_list_request,
    basic_db_list_request,
)


def test_published_json_rpc_basic(confd_published_json_rpc_access):
    """The ITDE-published HTTPS route supports read-only Basic JSON-RPC."""
    assert_db_list_response(
        basic_db_list_request(
            confd_published_json_rpc_access.endpoint,
            confd_published_json_rpc_access.username,
            confd_published_json_rpc_access.password,
        )
    )


def test_published_json_rpc_token(confd_published_json_rpc_access):
    """The published localhost route accepts the EXAConf authentication token."""
    assert_db_list_response(
        authentication_token_db_list_request(
            confd_published_json_rpc_access.endpoint,
            confd_published_json_rpc_access.token,
        )
    )
