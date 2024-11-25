import logging
from typing import List

from docker.models.containers import Container

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient


def remove_docker_container(containers: List[str]):
    """
    Removes the given container using docker API.
    """
    with ContextDockerClient() as docker_client:
        for container in containers:
            try:
                docker_client.containers.get(container).remove(force=True)
            except Exception as e:
                logging.error(e)


def default_bridge_ip_address(container: Container) -> str:
    container.reload()
    return container.attrs["NetworkSettings"]["Networks"]["bridge"]["IPAddress"]
