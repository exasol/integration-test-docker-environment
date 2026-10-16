"""Common wire-level helpers for the ConfD JSON-RPC access scenarios."""

import base64
import json
import ssl
import time
from dataclasses import dataclass
from urllib.request import (
    Request,
    urlopen,
)

import pytest
from docker.models.containers import Container

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient

_UNVERIFIED_TLS_CONTEXT = ssl._create_unverified_context()  # noqa: SLF001


@dataclass(frozen=True)
class ConfdJsonRpcAccess:
    """A ready-to-use JSON-RPC endpoint with both supported credentials."""

    endpoint: str
    username: str
    password: str
    token: str


def create_json_rpc_access(environment, endpoint: str) -> ConfdJsonRpcAccess:
    """Read both credentials for a JSON-RPC endpoint from an environment."""
    database_info = environment.environment_info.database_info
    confd_info = database_info.confd_info
    container_info = database_info.container_info
    assert confd_info is not None
    assert container_info is not None
    credentials = confd_info.read_credentials()
    with ContextDockerClient() as docker_client:
        container = docker_client.containers.get(container_info.container_name)
        token = _read_authentication_token(container)
    return ConfdJsonRpcAccess(
        endpoint=endpoint,
        username=credentials.username,
        password=credentials.password,
        token=token,
    )


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


def _read_authentication_token(container: Container) -> str:
    result = container.exec_run(
        "awk -F' = ' '/AuthenticationToken/ {print $2; exit}' /exa/etc/EXAConf"
    )
    if result.exit_code != 0 or not result.output.strip():
        pytest.fail("ConfD bearer-token test setup failed")
    return result.output.decode().strip()


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
