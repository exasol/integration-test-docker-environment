import json
import logging
import time

import requests

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.docker.container.utils import remove_docker_container
from exasol_integration_test_docker_environment.testing.utils import find_free_ports


class DockerRegistry:
    def __init__(self, name: str, ):
        self.name = name

    @property
    def repository_name(self):
        return f"{self.repository_prefix.lower()}/{self.name.lower()}"

    @property
    def repository_prefix(self):
        return "exaslct_test"

    def close(self):
        pass


class LocalDockerRegistry(DockerRegistry):
    def __init__(self, name: str, registry_container, registry_port):
        super().__init__(name)
        self._repository_prefix = f"localhost:{registry_port}"
        self._registry_container = registry_container
        self._registry_port = registry_port

    @property
    def repository_name(self):
        return f"{self._repository_prefix.lower()}/{self.name.lower()}"

    @property
    def repository_prefix(self):
        return self._repository_prefix

    @property
    def registry_port(self):
        return self._registry_port

    @property
    def registry_host(self):
        return "localhost"

    @property
    def registry_container(self):
        return self._registry_container

    def request_registry_images(self):
        url = f"http://{self.registry_host}:{self.registry_port}/v2/{self.name.lower()}/tags/list"
        result = requests.request("GET", url)
        images = json.loads(result.content.decode("UTF-8"))
        return images

    def request_registry_repositories(self):
        result = requests.request("GET", f"http://{self.registry_host}:{self.registry_port}/v2/_catalog/")
        repositories_ = json.loads(result.content.decode("UTF-8"))["repositories"]
        return repositories_

    def close(self):
        remove_docker_container([self.registry_container.id])


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

