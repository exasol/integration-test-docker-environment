from test.integration.cli_environment_common import (
    assert_db_container_started,
)


def test_db_container_started_bin(request):
    assert_db_container_started(request, "bin_context")
