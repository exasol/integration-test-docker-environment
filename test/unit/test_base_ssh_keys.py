import os
import platform
import pytest

from pathlib import Path
from exasol_integration_test_docker_environment.lib.base.ssh_access import SshFiles, SshKey


def test_create_file_and_permissions(tmp_path):
    ssh_files = SshFiles(tmp_path)
    SshKey.from_files(ssh_files)
    file = ssh_files.private_key
    assert file.exists()
    actual = oct(os.stat(file).st_mode)[-3:]
    expected = "666" if platform.system() == "Windows" else "600"
    assert expected == actual


def test_read_existing_file(tmp_path):
    ssh_files = SshFiles(tmp_path)
    testee = SshKey.from_files(ssh_files)
    other = SshKey.from_files(ssh_files)
    assert testee.private == other.private
