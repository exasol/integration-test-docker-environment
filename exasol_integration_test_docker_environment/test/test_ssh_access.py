import os
import pytest

from .conftest import find_container
from exasol_integration_test_docker_environment.lib.base.ssh_access import SshFiles


def test_generate_ssh_key_file(database):
    test_name = "test_generate_ssh_key_file"
    with database(
            name=test_name,
            additional_parameters = ["--db-os-access", "SSH"],
    ):
        files = SshFiles()
        container = find_container("db_container", test_name)
        command = container.exec_run("cat /root/.ssh/authorized_keys")
    assert files.private_key.exists()
    " itde-ssh-access" in command[1].decode("utf-8")
