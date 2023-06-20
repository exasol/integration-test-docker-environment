import contextlib
import fabric
import io
import os
import pytest

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.base.ssh_access import SshKey, SshKeyCache
from test.integration.helpers import container_named


def test_generate_ssh_key_file(api_database):
    params = { "db_os_access": "SSH" }
    with api_database(additional_parameters=params) as db:
        cache = SshKeyCache()
        container_name = db.environment_info.database_info.container_info.container_name
        with container_named(container_name) as container:
            command = container.exec_run("cat /root/.ssh/authorized_keys")
    assert cache.private_key.exists()
    assert " itde-ssh-access" in command[1].decode("utf-8")


def test_ssh_access(api_database, monkeypatch):
    params = { "db_os_access": "SSH" }
    with api_database(additional_parameters=params) as db:
        container_name = db.environment_info.database_info.container_info.container_name
        with container_named(container_name) as container:
            command = container.exec_run("cat /root/.ssh/authorized_keys")
        key = SshKey.from_cache()
        # Mock stdin to avoid ThreadException when reading from
        # stdin while stdout is capture by pytest.
        # See https://github.com/fabric/fabric/issues/2005
        monkeypatch.setattr('sys.stdin', io.StringIO(''))
        result = fabric.Connection(
            f"root@localhost:{db.ports.ssh}",
            connect_kwargs={ "pkey": key.private },
        ).run('ls /exa/etc/EXAConf')
        assert result.stdout == "/exa/etc/EXAConf\n"
