from test.integration.cli_environment_common import (
    assert_db_available,
)

from exasol_integration_test_docker_environment.lib.test_environment.parameter.docker_db_test_environment_parameter import (
    DbOsAccess,
)


def test_db_available_cli_docker_exec(request, fabric_stdin):
    assert_db_available(request, "cli_context", DbOsAccess.DOCKER_EXEC, False)
