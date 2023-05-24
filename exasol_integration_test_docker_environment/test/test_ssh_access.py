import os
import pytest

from .conftest import find_container
from exasol_integration_test_docker_environment.lib.base.ssh_access import (
    SshKey,
    SshFiles,
)


def test_generate_ssh_key_file(database):
    test_name = "test_generate_ssh_key_file"
    with database(
            name=test_name,
            additional_parameters = ["--db-os-access", "SSH"],
    ):
        files = SshFiles()
        container = find_container("db_container", test_name)
        check_mounted = container.exec_run("test -e /root/.ssh/authorized_keys")
    assert files.private_key.exists()
    assert files.authorized_keys_folder.exists()
    assert os.path.isdir(files.authorized_keys_folder)
    assert check_mounted[0] == 0
