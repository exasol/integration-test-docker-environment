import json
from test.integration.confd_access.json_rpc import authentication_token_db_list_request


def test_exaconf_token_is_used_as_bearer_token():
    request = authentication_token_db_list_request(
        "https://confd.example/rest", "encoded-token"
    )

    assert request.full_url == "https://confd.example/rest"
    assert request.get_header("Authorization") == "Bearer encoded-token"
    assert json.loads(request.data) == {
        "method": "job_start",
        "job": "db_list",
        "params": {"params": {}, "dry_run": False, "volatile": False},
    }
