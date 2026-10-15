"""Container-IP ConfD JSON-RPC integration scenarios."""

from test.integration.confd_access.json_rpc import (
    assert_db_list_response,
    authentication_token_db_list_request,
    basic_db_list_request,
    json_rpc_response,
)
from urllib.error import HTTPError

import pytest


def test_container_ip_json_rpc_basic(confd_container_ip_json_rpc_access):
    """A disposable Basic user can read, but not with an invalid password."""
    access = confd_container_ip_json_rpc_access
    assert_db_list_response(
        basic_db_list_request(access.endpoint, access.username, access.password)
    )
    invalid_password_request = basic_db_list_request(
        access.endpoint, access.username, access.password + "invalid"
    )
    with pytest.raises(HTTPError) as error:
        json_rpc_response(invalid_password_request)

    assert error.value.code in {401, 403}


def test_container_ip_json_rpc_token(confd_container_ip_json_rpc_access):
    """The direct container-IP route accepts the EXAConf authentication token."""
    assert_db_list_response(
        authentication_token_db_list_request(
            confd_container_ip_json_rpc_access.endpoint,
            confd_container_ip_json_rpc_access.token,
        )
    )
