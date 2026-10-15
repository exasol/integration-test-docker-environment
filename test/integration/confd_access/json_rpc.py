"""Common wire-level helpers for the ConfD JSON-RPC access scenarios."""

import base64
import json
import ssl
import time
from urllib.request import (
    Request,
    urlopen,
)

_UNVERIFIED_TLS_CONTEXT = ssl._create_unverified_context()  # noqa: SLF001


def basic_db_list_request(endpoint: str, username: str, password: str) -> Request:
    """Create a Basic-authenticated request for ConfD's read-only operation."""
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    return _db_list_request(endpoint, f"Basic {credentials}")


def authentication_token_db_list_request(endpoint: str, token: str) -> Request:
    """Create a request using the EXAConf bearer token."""
    return _db_list_request(endpoint, f"Bearer {token}")


def assert_db_list_response(request: Request) -> None:
    """Run ConfD's read-only database-list job to completion."""
    job_id = json_rpc_response(request)
    assert isinstance(job_id, str)

    for _ in range(30):
        time.sleep(0.5)
        payload = json_rpc_response(_job_result_request(request, job_id))
        assert isinstance(payload, dict)
        if payload["result_code"] != 5:
            assert payload["result_code"] == 0
            assert isinstance(payload["result_output"], list)
            return

    raise AssertionError("ConfD db_list job did not finish within 15 seconds")


def json_rpc_response(request: Request) -> object:
    """Execute a request using the disposable database TLS configuration."""
    with urlopen(request, context=_UNVERIFIED_TLS_CONTEXT, timeout=10) as response:
        assert response.status == 200
        return json.load(response)


def _db_list_request(endpoint: str, authorization: str) -> Request:
    return Request(
        endpoint,
        data=json.dumps(
            {
                "method": "job_start",
                "job": "db_list",
                "params": {"params": {}, "dry_run": False, "volatile": False},
            }
        ).encode(),
        headers={
            "Authorization": authorization,
            "Content-Type": "application/json",
        },
        method="POST",
    )


def _job_result_request(start_request: Request, job_id: str) -> Request:
    authorization = start_request.get_header("Authorization")
    assert authorization is not None
    return Request(
        start_request.full_url,
        data=json.dumps(
            {"method": "job_result", "params": {"job_id": job_id}}
        ).encode(),
        headers={"Authorization": authorization, "Content-Type": "application/json"},
        method="POST",
    )
