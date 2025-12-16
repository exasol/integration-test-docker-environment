from exasol.bucketfs import Service

from exasol_integration_test_docker_environment.lib.test_environment.ports import (
    find_free_ports,
)


def _bucketfs_access(protocol: str, port: int, verify: str | None = None):
    URL = f"{protocol}://localhost:{port}"
    CREDENTIALS = {"default": {"username": "w", "password": "write"}}

    bucketfs = Service(URL, CREDENTIALS, verify=False if verify is None else verify)
    buckets = [bucket for bucket in bucketfs]
    assert len(buckets) > 0


def _assert_bucketfs(http_port: int, https_port: int, verify: str | None = None):
    _bucketfs_access("http", http_port, verify)
    _bucketfs_access("https", https_port, verify)


def test_default_ports(api_context):
    with api_context() as db:
        _assert_bucketfs(db.ports.bucketfs_http, db.ports.bucketfs_https)


def test_custom_ports(api_context):
    http_port, https_port = find_free_ports(2)
    additional_parameters = {
        "bucketfs_port_forward": http_port,
        "bucketfs_https_port_forward": https_port,
    }
    with api_context(
        additional_parameters=additional_parameters,
    ):
        _assert_bucketfs(http_port, https_port)
