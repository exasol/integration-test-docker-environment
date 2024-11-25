import logging
from typing import Iterable

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient


def remove_docker_networks(networks: Iterable[str]):
    """
    Removes the given networks using docker API.
    """
    with ContextDockerClient() as docker_client:
        for network in networks:
            try:
                docker_client.networks.get(network).remove()
            except Exception as e:
                logging.error(e)
