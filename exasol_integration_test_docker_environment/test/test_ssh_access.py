import os
import pytest

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.base.ssh_access import (
    SshKey,
    SshFiles,
)


def run_in_db_container(env_name: str, command: str):
    is_db = lambda c: env_name in c.name and "db_container" in c
    with ContextDockerClient() as client:
        containers = [c for c in client.containers.list() if is_db(c)]
        db_container = client.containers.get(containers[0])
        return db_container.exec_run(command)


def test_generate_ssh_key_file(database):
    with database(
            additional_parameters = ["--db-os-access", "SSH"],
    ) as db:
        files = SshFiles()
        print(f'name of cli isolation environment: "{db.name}"')
        check_mounted = run_in_db_container(db.name, "test -e /root/.ssh/authorized_keys")
    assert files.private_key.exists()
    assert files.authorized_keys_folder.exists()
    assert os.path.isdir(files.authorized_keys_folder)
    assert check_mounted[0] == 0
