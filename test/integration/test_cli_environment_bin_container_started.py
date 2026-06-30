from test.integration.cli_environment_common import (
    assert_db_container_started,
)


def test_db_container_started_bin(bin_context):
    assert_db_container_started(bin_context)
