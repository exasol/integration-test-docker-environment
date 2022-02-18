"""
The doctor module provides functionality to check the health of the `exasol_integration_test_docker_environment`
package and also provide help to find potential fixes.
"""
from enum import Enum
from typing import Iterator

import docker
from docker.errors import DockerException


class ErrorCodes(Enum):
    """This doctors ICD codes"""

    Unknown = "Unknown issue"
    UnixSocketNotAvailable = "Could not find unix socket to connect to"


def recommend_treatment(error_code) -> str:
    """Get treatment advice based on the error_code"""
    return {
        ErrorCodes.Unknown: "You are sick but this symptoms are unknown, please contact the maintainer.",
        ErrorCodes.UnixSocketNotAvailable: "Make sure you DOCKER_HOST environment variable is configured correctly.",
    }[error_code]


def diagnose_docker_daemon_not_available() -> Iterator[ErrorCodes]:
    """Diagnose reasons why docker deamon is not available"""

    def _is_unix_socket_issue(msg):
        return "FileNotFoundError(2, 'No such file or directory')" in msg

    errors = set()
    try:
        _docker = docker.from_env()
    except DockerException as ex:
        msg = f"{ex}"
        if _is_unix_socket_issue(msg):
            errors.add(ErrorCodes.UnixSocketNotAvailable)
        if len(errors) == 0:
            errors.add(ErrorCodes.Unknown)
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


def health_checkup() -> Iterator[ErrorCodes]:
    """
    Runs all known examinations

    return an iterator of error codes specifying which problems have been identified.
    """
    examinations = [(is_docker_daemon_available, diagnose_docker_daemon_not_available)]
    for is_fine, diagnosis in examinations:
        if not is_fine():
            for error_code in diagnosis():
                yield error_code
