import contextlib
import pytest

from typing import Iterator, List, Optional

from exasol_integration_test_docker_environment.testing import utils
from exasol_integration_test_docker_environment.testing \
   .exaslct_test_environment import ExaslctTestEnvironment
from exasol_integration_test_docker_environment.testing \
   .exaslct_test_environment import SpawnedTestEnvironments
from exasol_integration_test_docker_environment.lib.base.ssh_access import SshKey

# from fake import SpawnedTestEnvironments, ExaslctTestEnvironment, utils

@contextlib.contextmanager
def database(itde_test_isolation: ExaslctTestEnvironment,
             name: Optional[str] = None,
             additional_parameters: Optional[List[str]] = None
             ) -> Iterator[SpawnedTestEnvironments]:
    name = name if name else itde_test_isolation.name
    spawned = itde_test_isolation.spawn_docker_test_environments(
        name=name,
        additional_parameter=additional_parameters,
    )
    try:
        yield spawned
    finally:
        utils.close_environments(spawned)


def test_generate_ssh_key_file(itde_cli_test_isolation):
    with database(
            itde_cli_test_isolation,
            additional_parameters = ["--db-os-access", "SSH"],
    ) as db:
        file = SshKey.default_folder() / "id_rsa"
    assert file.exists()
