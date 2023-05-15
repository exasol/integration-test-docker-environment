import os
import platform
import sys
import pytest

from pathlib import Path
from exasol_integration_test_docker_environment.lib.base.ssh_access import SshKey


def test_create_file_and_permissions(tmp_path):
    testee = SshKey.from_folder(tmp_path)
    file = tmp_path / "id_rsa"
    assert file.exists()
    actual = oct(os.stat(file).st_mode)[-3:]
    expected = "666" if platform.system() == "Windows" else "600"
    assert expected == actual


def test_read_existing_file(tmp_path):
    testee = SshKey.from_folder(tmp_path)
    other = SshKey.from_folder(tmp_path)
    assert testee.private == other.private

