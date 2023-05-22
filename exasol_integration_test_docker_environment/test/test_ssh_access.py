import pytest

from exasol_integration_test_docker_environment.lib.base.ssh_access import SshKey


def test_generate_ssh_key_file(itde_cli_test_isolation):
    with database(
            itde_test_isolation,
            additional_parameter = ["--db-os-access", "SSH"],
    ) as db:
        file = SshKey.default_folder() / "id_rsa"
    assert file.exists()
