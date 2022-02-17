"""
The doctor module provides functionality to check the health of the `exasol_integration_test_docker_environment`
package and also provide help to find potential fixes.
"""
from enum import Enum, auto

import docker
from docker.errors import DockerException


class Icd(Enum):
    """This doctors ICD codes"""

    Unknown = "Unknown issue"
    UnixSocketNotAvailable = "Could not find unix socket to connect to"


def recommend_treatment(icd):
    """Get treatment advice based on the icd"""
    return {
        Icd.Unknown: "You are sick but this symptoms are unknown, please contact the maintainer.",
        Icd.UnixSocketNotAvailable: "Make sure you DOCKER_HOST environment variable is configured correctly.",
    }[icd]


def diagnose_docker_daemon_not_available():
    """Diagnose reasons why docker deamon is not available"""

    def _is_unix_socket_issue(msg):
        return "FileNotFoundError(2, 'No such file or directory')" in msg

    icds = set()
    try:
        _docker = docker.from_env()
    except DockerException as ex:
        msg = f"{ex}"
        if _is_unix_socket_issue(msg):
            icds.add(Icd.UnixSocketNotAvailable)
        if len(icds) == 0:
            icds.add(Icd.Unknown)
    return icds


def is_docker_daemon_available():
    """
    Checks weather or not the docker daemon is available.
    """
    try:
        _docker = docker.from_env()
    except DockerException:
        return False
    return True


def health_checkup():
    """
    Runs all known examinations

    return icd's which have been identified.
    rtype: Generator
    """
    examinations = [(is_docker_daemon_available, diagnose_docker_daemon_not_available)]
    for is_fine, diagnosis in examinations:
        if not is_fine():
            for icd in diagnosis():
                yield icd
