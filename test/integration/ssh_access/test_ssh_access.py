from test.integration.helpers import container_named

import fabric

from exasol_integration_test_docker_environment.lib.base.ssh_access import SshKey


def test_ssh_access(api_context, fabric_stdin):
    params = {"db_os_access": "SSH"}
    with api_context(additional_parameters=params) as db:
        container_name = db.environment_info.database_info.container_info.container_name
        with container_named(container_name) as container:
            command = container.exec_run("cat /root/.ssh/authorized_keys")
        key = SshKey.from_cache()
        result = fabric.Connection(
            f"root@localhost:{db.ports.ssh}",
            connect_kwargs={"pkey": key.private},
        ).run("ls /exa/etc/EXAConf")
        assert result.stdout == "/exa/etc/EXAConf\n"
