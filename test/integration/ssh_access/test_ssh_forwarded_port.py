from exasol_integration_test_docker_environment.lib.base.db_os_executor import (
    SshExecFactory,
)


def test_ssh_fixture_uses_reachable_forwarded_port(api_context, fabric_stdin):
    with api_context(additional_parameters={"db_os_access": "SSH"}) as db:
        database_info = db.environment_info.database_info
        assert database_info.forwarded_ports is not None
        assert database_info.forwarded_ports.ssh == db.ports.ssh

        with SshExecFactory.from_database_info(database_info).executor() as executor:
            executor.prepare()
            exit_code, output = executor.exec("test -f /exa/etc/EXAConf")

    assert exit_code == 0
    assert output == b""
