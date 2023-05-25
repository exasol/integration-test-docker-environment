import os
import pytest

from conftest import find_container
from exasol_integration_test_docker_environment.lib.base.ssh_access import SshFiles


def test_generate_ssh_key_file(api_database):
    params = { "db_os_access": "SSH" }
    with api_database(additional_parameters=params) as db:
        files = SshFiles()
        container = find_container("db_container", db.name)
        command = container.exec_run("cat /root/.ssh/authorized_keys")
    assert files.private_key.exists()
    " itde-ssh-access" in command[1].decode("utf-8")
