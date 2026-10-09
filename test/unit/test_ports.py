from exasol_integration_test_docker_environment.lib.test_environment.parameter.docker_db_test_environment_parameter import (
    DbOsAccess,
)
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


def test_default_port_bindings_are_limited_to_loopback():
    mapping = SpawnTestDockerDatabase._port_mapping(
        type("Task", (), {"port_bind_address": None})(),
        Ports.default_ports,
        Ports(1, 2, 3, 4, confd=5),
    )

    assert mapping["443/tcp"] == ("127.0.0.1", 5)
    assert mapping["8563/tcp"] == ("127.0.0.1", 1)


def test_port_bind_address_applies_to_all_forwarded_ports():
    task = type("Task", (), {"port_bind_address": "192.0.2.1"})()
    mapping = SpawnTestDockerDatabase._port_mapping(
        task, Ports.default_ports, Ports(1, 2, 3, 4, confd=5)
    )

    assert mapping["443/tcp"] == ("192.0.2.1", 5)
    assert mapping["8563/tcp"] == ("192.0.2.1", 1)
    assert mapping["2580/tcp"] == ("192.0.2.1", 2)
    assert mapping["22/tcp"] == ("192.0.2.1", 3)
    assert mapping["2581/tcp"] == ("192.0.2.1", 4)


def _spawn_database_task(db_os_access, ssh_port_forward=None):
    return SpawnTestDockerDatabase(
        job_id="test-job",
        environment_name="test-environment",
        db_container_name="test-database",
        network_info=None,
        ip_address_index_in_subnet=0,
        additional_db_parameter=(),
        docker_environment_variables=(),
        accelerator=(),
        docker_db_image_version="8.29.13",
        db_os_access=db_os_access,
        ssh_port_forward=(None if ssh_port_forward is None else str(ssh_port_forward)),
    )


def test_docker_exec_does_not_forward_an_explicit_ssh_port():
    task = _spawn_database_task(DbOsAccess.DOCKER_EXEC, ssh_port_forward=30123)

    assert task.ssh_port_forward is None
    assert task.forwarded_ports.ssh is None


def test_ssh_uses_explicit_port_forward():
    task = _spawn_database_task(DbOsAccess.SSH, ssh_port_forward=30123)

    assert task.ssh_port_forward == "30123"
    assert task.forwarded_ports.ssh == 30123


def test_ssh_selects_a_port_forward_when_unspecified(monkeypatch):
    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.test_environment.spawn_test_database.find_free_ports",
        lambda count: [30123],
    )

    task = _spawn_database_task(DbOsAccess.SSH)

    assert task.ssh_port_forward == "30123"
    assert task.forwarded_ports.ssh == 30123
