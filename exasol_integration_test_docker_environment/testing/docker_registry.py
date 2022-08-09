import json
import logging
import time
from dataclasses import dataclass

import requests

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.docker.container.utils import remove_docker_container
from exasol_integration_test_docker_environment.testing.utils import find_free_ports


@dataclass
class DockerRegistryDescription:
    """
    Represents a docker registry, consisting of a prefix and the name. The prefix can also be a hostname and port,
    thus indicating a custom repository (not Dockerhub).
    repository_name returns the fully qualified name which can be used to push/pull images.
    """
    name: str
    repository_prefix: str

    @property
    def repository_name(self):
        return f"{self.repository_prefix.lower()}/{self.name.lower()}"


def default_docker_registry_description(name: str) -> DockerRegistryDescription:
    return DockerRegistryDescription(name=name, repository_prefix="exaslct_test")


class LocalDockerRegistry:
    def __init__(self, name: str, registry_container, registry_port):
        self._name = name
        self._registry_container = registry_container
        self._registry_port = registry_port

    @property
    def docker_registry_description(self):
        return DockerRegistryDescription(name=self._name, repository_prefix=f"localhost:{self._registry_port}")

    def request_registry_images(self):
        url = f"http://localhost:{self._registry_port}/v2/{self._name.lower()}/tags/list"
        result = requests.request("GET", url)
        images = json.loads(result.content.decode("UTF-8"))
        return images

    def request_registry_repositories(self):
        result = requests.request("GET", f"http://localhost:{self._registry_port}/v2/_catalog/")
        repositories_ = json.loads(result.content.decode("UTF-8"))["repositories"]
        return repositories_

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        remove_docker_container([self._registry_container.id])


def create_local_registry(name: str) -> LocalDockerRegistry:
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
        return LocalDockerRegistry(name, registry_container, registry_port)

