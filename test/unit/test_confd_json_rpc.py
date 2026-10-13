from test.integration.confd_access.json_rpc import authentication_token_db_list_request


def test_exaconf_token_is_used_as_preencoded_basic_credentials():
    request = authentication_token_db_list_request(
        "https://confd.example/RPC2", "encoded-token"
    )

    assert request.get_header("Authorization") == "Basic encoded-token"
