from test.integration.cli_environment_common import (
    assert_db_container_started,
)


def test_db_container_started_cli(request):
    assert_db_container_started(request, "cli_context")
