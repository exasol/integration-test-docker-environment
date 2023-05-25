import os
import pytest

from .conftest import find_container
from exasol_integration_test_docker_environment.lib.base.ssh_access import SshFiles


def test_generate_ssh_key_file_cli(cli_database):
    test_name = "test_generate_ssh_key_file"
    with cli_database(
            name=test_name,
            additional_parameters = ["--db-os-access", "SSH"],
    ):
        # slc_test wenn nicht None
        # else on_ho
        files = SshFiles()
        container = find_container("db_container", test_name)
        command = container.exec_run("cat /root/.ssh/authorized_keys")
    assert files.private_key.exists()
    " itde-ssh-access" in command[1].decode("utf-8")

# # use api
# def test_generate_ssh_key_file(api_database):
#     pass
