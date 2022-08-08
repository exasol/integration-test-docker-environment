import logging
from typing import List

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient


def remove_docker_volumes(volumes: List[str]):
    """
    Removes the given volumes using docker API.
    """
    with ContextDockerClient() as docker_client:
        for volume in volumes:
            try:
                docker_client.volumes.get(volume).remove(force=True)
            except Exception as e:
                logging.error(e)
