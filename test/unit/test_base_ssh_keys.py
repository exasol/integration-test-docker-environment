import os
import platform
from pathlib import Path

import pytest

from exasol_integration_test_docker_environment.lib.base.ssh_access import (
    SshKey,
    SshKeyCache,
)


def test_create_file_and_permissions(tmp_path):
    SshKey.from_cache(tmp_path)
    file = SshKeyCache(tmp_path).private_key
    assert file.exists()
    actual = oct(os.stat(file).st_mode)[-3:]
    expected = "666" if platform.system() == "Windows" else "600"
    assert expected == actual


def test_read_existing_file(tmp_path):
    testee = SshKey.from_cache(tmp_path)
    other = SshKey.from_cache(tmp_path)
    assert testee.private == other.private
