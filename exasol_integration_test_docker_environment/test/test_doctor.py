import os
import unittest
from contextlib import contextmanager

from exasol_integration_test_docker_environment.doctor import (
    Icd,
    diagnose_docker_daemon_not_available,
    is_docker_daemon_available,
)


@contextmanager
def temporary_env(env_vars):
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


class IsDockerDaemonAvailableTest(unittest.TestCase):
    """
    Attention: this tests require docker.
    """

    def test_docker_connection_attempt_on_non_existing_unix_socket_returns_false(self):
        """
        Regression:  https://github.com/exasol/integration-test-docker-environment/issues/17

        Cause: If docker tries to use a unix socket to connect to the docker deamon but the associated
               file of the unix socket is not existent, creating a docker client using
               `docker.from_env()` will fail with an exception.
        """
        env = {"DOCKER_HOST": "unix:///var/non/existent/path"}
        with temporary_env(env):
            self.assertFalse(is_docker_daemon_available())

    def test_successful_connection_to_the_daemon(self):
        self.assertTrue(is_docker_daemon_available())


class DiagnoseDockerDaemonNotAvailable(unittest.TestCase):
    """
    Attention: this tests require docker.
    """

    def test_non_existing_unix_socket(self):
        expected = {Icd.UnixSocketNotAvailable}
        env = {"DOCKER_HOST": "unix:///var/non/existent/path"}
        with temporary_env(env):
            self.assertEqual(expected, diagnose_docker_daemon_not_available())

    def test_unknown_error(self):
        expected = {Icd.Unknown}
        env = {"DOCKER_HOST": "https://foobar"}
        with temporary_env(env):
            self.assertEqual(expected, diagnose_docker_daemon_not_available())


if __name__ == "__main__":
    unittest.main()
