"""
The doctor module provides functionality to check the health of the `exasol_integration_test_docker_environment`
package and also provide help to find potential fixes.
"""

import sys
from collections.abc import (
    Callable,
    Iterable,
)
from enum import Enum

import docker
from docker.errors import DockerException
from exasol.error import ExaError

SUPPORTED_PLATFORMS = ["linux", "darwin"]


class HealthProblem(Enum):
    Unknown = ExaError(
        "E-ITDE-0",
        "Unknown issue.",
        ["An unknown error occurred, please contact the maintainer."],
        {},
    )

    UnixSocketNotAvailable = ExaError(
        "E-ITDE-1",
        "Could not find unix socket to connect to.",
        ["Make sure environment variable DOCKER_HOST is configured correctly."],
        {},
    )

    TargetPlatformNotSupported = ExaError(
        "E-ITDE-2",
        "The platform ITDE is running on is not supported.",
        ["Make sure you are using one of the following platforms: [linux, darwin]."],
        {},
    )


def diagnose_docker_daemon_not_available() -> Iterable[HealthProblem]:
    """Diagnose reasons why docker deamon is not available"""

    def _is_unix_socket_issue(message: str) -> bool:
        return "FileNotFoundError(2, 'No such file or directory')" in message

    errors = []
    try:
        _docker = docker.from_env()
    except DockerException as ex:
        msg = f"{ex}"
        if _is_unix_socket_issue(msg):
            errors.append(HealthProblem.UnixSocketNotAvailable)
        if len(errors) == 0:
            errors.append(HealthProblem.Unknown)
    return errors


def is_docker_daemon_available() -> bool:
    """
    Checks weather or not the docker daemon is available.
    """
    try:
        _docker = docker.from_env()
    except DockerException:
        return False
    return True


def is_supported_platform() -> bool:
    """
    Checks weather or not the current platform is supported.
    """
    return sys.platform in SUPPORTED_PLATFORMS


def health_checkup() -> Iterable[HealthProblem]:
    """
    Runs all known examinations

    return an iterator of error codes specifying which problems have been identified.
    """
    check_function = Callable[[], bool]
    diagnosis_function = Callable[[], Iterable[HealthProblem]]
    examinations: list[tuple[check_function, diagnosis_function]] = [
        (is_docker_daemon_available, diagnose_docker_daemon_not_available),
        (is_supported_platform, lambda: [HealthProblem.TargetPlatformNotSupported]),
    ]
    for is_fine, diagnosis in examinations:
        if not is_fine():
            yield from diagnosis()
