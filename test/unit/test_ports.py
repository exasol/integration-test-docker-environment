from exasol_integration_test_docker_environment.lib.test_environment.ports import Ports
from exasol_integration_test_docker_environment.lib.test_environment.spawn_test_database import (
    SpawnTestDockerDatabase,
)


def test_forward_ports():
    p = Ports.forward
    assert p.database == 8563
    assert p.bucketfs == 2580
    assert p.bucketfs_http == 2580
    assert p.ssh == 20002
    assert p.bucketfs_https == 2581
    assert p.confd is None


def test_default_ports():
    p = Ports.default_ports
    assert p.database == 8563
    assert p.bucketfs == 2580
    assert p.bucketfs_http == 2580
    assert p.ssh == 22
    assert p.bucketfs_https == 2581
    assert p.confd == 443


def test_external_ports():
    p = Ports.external
    assert p.database == 8563
    assert p.bucketfs == 2580
    assert p.bucketfs_http == 2580
    assert p.ssh is None
    assert p.bucketfs_https == 2581
    assert p.confd is None


def test_confd_forwarding_is_limited_to_loopback():
    mapping = SpawnTestDockerDatabase._port_mapping(
        object(), Ports.default_ports, Ports(1, 2, 3, 4, confd=5)
    )

    assert mapping["443/tcp"] == ("127.0.0.1", 5)
    assert mapping["8563/tcp"] == 1
