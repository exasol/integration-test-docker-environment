"""Container-IP ConfD JSON-RPC Basic-auth integration scenario."""

from test.integration.confd_access.json_rpc import (
    assert_db_list_response,
    basic_db_list_request,
    json_rpc_response,
)
from urllib.error import HTTPError

import pytest


def test_container_ip_json_rpc_basic(confd_container_ip_json_rpc_basic_access):
    """A disposable Basic user can read, but not with an invalid password."""
    with confd_container_ip_json_rpc_basic_access() as access:
        endpoint = f"https://{access.host}:443/rest"
        assert_db_list_response(
            basic_db_list_request(endpoint, access.username, access.password)
        )
        invalid_password_request = basic_db_list_request(
            endpoint,
            access.username,
            access.password + "invalid",
        )
        with pytest.raises(HTTPError) as error:
            json_rpc_response(invalid_password_request)

    assert error.value.code in {401, 403}
