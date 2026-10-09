from exasol_integration_test_docker_environment.lib.base.db_os_executor import (
    SshExecFactory,
)


def test_ssh_fixture_uses_reachable_forwarded_port(api_context, fabric_stdin):
    with api_context(additional_parameters={"db_os_access": "SSH"}) as db:
        database_info = db.environment_info.database_info
        assert database_info.forwarded_ports is not None
        assert database_info.forwarded_ports.ssh == db.ports.ssh

        with SshExecFactory.for_host(database_info).executor() as executor:
            executor.prepare()
            exit_code, output = executor.exec("test -f /exa/etc/EXAConf")

    assert exit_code == 0
    assert output == b""


def test_ssh_fixture_normalizes_wildcard_forwarded_port(
    api_context, fabric_stdin
):
    """SSH uses loopback when Docker publishes the port on every IPv4 address."""
    with api_context(
        additional_parameters={
            "db_os_access": "SSH",
            "port_bind_address": "0.0.0.0",
        }
    ) as db:
        database_info = db.environment_info.database_info
        published_port = database_info.published_port("ssh")
        assert published_port is not None
        assert published_port.local_endpoint() == ("127.0.0.1", db.ports.ssh)

        with SshExecFactory.for_host(database_info).executor() as executor:
            executor.prepare()
            exit_code, output = executor.exec("test -f /exa/etc/EXAConf")

    assert exit_code == 0
    assert output == b""
