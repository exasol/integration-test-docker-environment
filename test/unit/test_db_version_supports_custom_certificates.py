import pytest

from exasol_integration_test_docker_environment.lib.test_environment.db_version import (
    db_version_supports_custom_certificates,
)


@pytest.mark.parametrize(
    "version,expected",
    [
        ("default", True),
        (None, True),
        ("7.0.5", False),
        ("7.0.14", True),
        ("7.1.3", True),
        ("7.1.3-d1", True),
    ],
)
def test_db_version_supports_custom_certificates(version, expected):
    assert db_version_supports_custom_certificates(version) == expected


def test_throw_error():
    with pytest.raises(ValueError):
        db_version_supports_custom_certificates("7abc")
