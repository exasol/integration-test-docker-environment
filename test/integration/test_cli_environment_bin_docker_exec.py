from test.integration.cli_environment_common import (
    assert_db_available,
)

from exasol_integration_test_docker_environment.lib.test_environment.parameter.docker_db_test_environment_parameter import (
    DbOsAccess,
)


def test_db_available_bin_docker_exec(bin_context, fabric_stdin):
    assert_db_available(bin_context, DbOsAccess.DOCKER_EXEC, False)
