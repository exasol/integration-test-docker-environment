import os
from collections.abc import Generator
from contextlib import contextmanager
from unittest import mock
from unittest.mock import patch

import pytest

from exasol_integration_test_docker_environment.doctor import (
    SUPPORTED_PLATFORMS,
    HealthProblem,
    diagnose_docker_daemon_not_available,
    is_docker_daemon_available,
    is_supported_platform,
)


def test_docker_connection_attempt_on_non_existing_unix_socket_returns_false(
    monkeypatch,
):
    """
    Regression:  https://github.com/exasol/integration-test-docker-environment/issues/17

    Cause: If docker tries to use a unix socket to connect to the docker deamon but the associated
           file of the unix socket is not existent, creating a docker client using
           `docker.from_env()` will fail with an exception.
    """
    monkeypatch.setitem(os.environ, "DOCKER_HOST", "unix:///var/non/existent/path")
    assert not is_docker_daemon_available()


def test_successful_connection_to_the_daemon():
    """
    This test requires a docker service to be available on the machine executing the tests.
    """
    assert is_docker_daemon_available()


def test_non_existing_unix_socket(monkeypatch):
    expected = [HealthProblem.UnixSocketNotAvailable]
    monkeypatch.setitem(os.environ, "DOCKER_HOST", "unix:///var/non/existent/path")
    assert expected == diagnose_docker_daemon_not_available()


def test_unknown_health_problem(monkeypatch):
    expected = [HealthProblem.Unknown]
    monkeypatch.setitem(os.environ, "DOCKER_HOST", "https://foobar")
    assert expected == diagnose_docker_daemon_not_available()


@pytest.mark.parametrize("platform", SUPPORTED_PLATFORMS)
def test_target_platform_is_supported(platform):
    with patch("sys.platform", platform):
        assert is_supported_platform()


def test_target_platform_is_not_supported():
    with patch("sys.platform", "unsupported-platform"):
        assert not is_supported_platform()
