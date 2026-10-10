"""Common wire-level helpers for the ConfD JSON-RPC access scenarios."""

import base64
import json
import ssl
from urllib.request import (
    Request,
    urlopen,
)

_REQUEST_ID = "itde-confd-db-list"
_UNVERIFIED_TLS_CONTEXT = ssl._create_unverified_context()  # noqa: SLF001


def basic_db_list_request(endpoint: str, username: str, password: str) -> Request:
    """Create a Basic-authenticated request for ConfD's read-only operation."""
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    return _db_list_request(endpoint, f"Basic {credentials}")


def bearer_token_db_list_request(endpoint: str, token: str) -> Request:
    """Create a bearer-token request for the legacy container-IP experiment."""
    return _db_list_request(endpoint, f"Bearer {token}")


def assert_db_list_response(request: Request) -> None:
    """Verify a successful, correlated response without exposing credentials."""
    payload = json_rpc_response(request)

    assert payload["id"] == _REQUEST_ID
    assert "error" not in payload


def json_rpc_response(request: Request) -> dict[str, object]:
    """Execute a request using the disposable database TLS configuration."""
    with urlopen(request, context=_UNVERIFIED_TLS_CONTEXT, timeout=10) as response:
        assert response.status == 200
        return json.load(response)


def _db_list_request(endpoint: str, authorization: str) -> Request:
    return Request(
        endpoint,
        data=json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "db_list",
                "params": {},
                "id": _REQUEST_ID,
            }
        ).encode(),
        headers={
            "Authorization": authorization,
            "Content-Type": "application/json",
        },
        method="POST",
    )
