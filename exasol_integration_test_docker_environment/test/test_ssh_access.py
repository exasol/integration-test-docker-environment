import os
import pytest

from exasol_integration_test_docker_environment.lib.base.ssh_access import (
    SshKey,
    SshFiles,
)


def test_generate_ssh_key_file(database):
    with database(
            additional_parameters = ["--db-os-access", "SSH"],
    ):
        files = SshFiles()
    assert files.private_key.exists()
    assert files.authorized_keys_folder.exists()
    assert os.path.isdir(files.authorized_keys_folder)
