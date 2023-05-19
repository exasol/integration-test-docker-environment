import pytest

from exasol_integration_test_docker_environment.lib.base.ssh_access import SshKey


def test_generate_ssh_key_file(slc_environment):
    file = SshKey.default_folder() / "id_rsa"
    assert file.exists()
