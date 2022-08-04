import logging
import time
from typing import Tuple, Union

from docker.models.resource import Model

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.testing.utils import find_free_ports


def create_registry(name: str) -> Tuple[Union[Model, None, bytes], str, int]:
    registry_port = find_free_ports(1)[0]
    registry_container_name = name.replace("/", "_") + "_registry"
    with ContextDockerClient() as docker_client:
        logging.debug("Start pull of registry:2")
        docker_client.images.pull(repository="registry", tag="2")
        logging.debug(f"Start container of {registry_container_name}")
        try:
            docker_client.containers.get(registry_container_name).remove(force=True)
        except:
            pass
        registry_container = docker_client.containers.run(
            image="registry:2", name=registry_container_name,
            ports={5000: registry_port},
            detach=True
        )
        time.sleep(10)
        logging.debug(f"Finished start container of {registry_container_name}")
        return registry_container, "localhost", registry_port
