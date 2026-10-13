"""Published-port ConfD JSON-RPC Basic-auth integration scenario."""

from test.integration.confd_access.json_rpc import (
    assert_db_list_response,
    basic_db_list_request,
)


def test_published_json_rpc_basic(confd_published_json_rpc_basic_access):
    """The ITDE-published HTTPS route supports read-only Basic JSON-RPC."""
    with confd_published_json_rpc_basic_access() as access:
        assert_db_list_response(
            basic_db_list_request(access.endpoint, access.username, access.password)
        )
