import os
import unittest
from collections.abc import Generator
from contextlib import contextmanager
from typing import Callable
from unittest.mock import patch

import pytest

from exasol_integration_test_docker_environment.doctor import (
    SUPPORTED_PLATFORMS,
    HealthProblem,
    diagnose_docker_daemon_not_available,
    is_docker_daemon_available,
    is_supported_platform,
)


@pytest.fixture
def temporary_env_factory() -> Callable[[dict], Generator[os._Environ, None, None]]:
    """
    Creates a temporary environment factory that returns a generator that yields a temporary environment.
    """

    @contextmanager
    def temporary_env_factory(env_vars: dict) -> Generator[os._Environ, None, None]:
        """
        Creates a temporary environment, containing the current environment variables.

        :param env_vars: to be updated within the temporary environment.

        :return: the temporary environment variables in use
        """
        old_env = dict(os.environ)
        os.environ.update(env_vars)
        yield os.environ
        os.environ.clear()
        os.environ.update(old_env)

    return temporary_env_factory


def test_docker_connection_attempt_on_non_existing_unix_socket_returns_false(
    temporary_env_factory,
):
    """
    Regression:  https://github.com/exasol/integration-test-docker-environment/issues/17

    Cause: If docker tries to use a unix socket to connect to the docker deamon but the associated
           file of the unix socket is not existent, creating a docker client using
           `docker.from_env()` will fail with an exception.
    """
    env = {"DOCKER_HOST": "unix:///var/non/existent/path"}
    with temporary_env_factory(env):
        assert not is_docker_daemon_available()


def test_successful_connection_to_the_daemon():
    """
    Attention: this test require docker.
    """
    assert is_docker_daemon_available()


def test_non_existing_unix_socket(temporary_env_factory):
    expected = [HealthProblem.UnixSocketNotAvailable]
    env = {"DOCKER_HOST": "unix:///var/non/existent/path"}
    with temporary_env_factory(env):
        assert expected == diagnose_docker_daemon_not_available()


def test_unknown_health_problem(temporary_env_factory):
    expected = [HealthProblem.Unknown]
    env = {"DOCKER_HOST": "https://foobar"}
    with temporary_env_factory(env):
        assert expected == diagnose_docker_daemon_not_available()


@pytest.mark.parametrize("platform", SUPPORTED_PLATFORMS)
def test_target_platform_is_supported(platform):
    with patch("sys.platform", platform):
        assert is_supported_platform()


def test_target_platform_is_not_supported():
    with patch("sys.platform", "unsupported-platform"):
        assert not is_supported_platform()
