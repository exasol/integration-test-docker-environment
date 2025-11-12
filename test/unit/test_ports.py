from exasol_integration_test_docker_environment.lib.test_environment.ports import Ports


def test_forward_ports():
    p = Ports.forward
    assert p.database == 8563
    assert p.bucketfs == 2580
    assert p.bucketfs_http == 2580
    assert p.ssh == 20002
    assert p.bucketfs_https == 2581


def test_default_ports():
    p = Ports.default_ports
    assert p.database == 8563
    assert p.bucketfs == 2580
    assert p.bucketfs_http == 2580
    assert p.ssh == 22
    assert p.bucketfs_https == 2581


def test_external_ports():
    p = Ports.external
    assert p.database == 8563
    assert p.bucketfs == 2580
    assert p.bucketfs_http == 2580
    assert p.ssh is None
    assert p.bucketfs_https == 2581
