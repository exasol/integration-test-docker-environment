import json
import logging
import time

import requests

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.docker.container.utils import (
    remove_docker_container,
)
from exasol_integration_test_docker_environment.lib.test_environment.ports import (
    find_free_ports,
)


def default_docker_repository_name(env_name: str) -> str:
    return f"exaslct_test/{env_name.lower()}"


class LocalDockerRegistry:
    def __init__(self, name: str, registry_container, registry_port):
        self._name = name
        self._registry_container = registry_container
        self._registry_port = registry_port

    @property
    def name(self):
        return f"localhost:{self._registry_port}/{self._name.lower()}"

    @property
    def images(self):
        url = (
            f"http://localhost:{self._registry_port}/v2/{self._name.lower()}/tags/list"
        )
        result = requests.request("GET", url)
        images = json.loads(result.content.decode("UTF-8"))
        return images

    @property
    def repositories(self):
        result = requests.request(
            "GET", f"http://localhost:{self._registry_port}/v2/_catalog/"
        )
        repositories_ = json.loads(result.content.decode("UTF-8"))["repositories"]
        return repositories_


class LocalDockerRegistryContextManager:
    def __init__(self, name: str):
        self._name = name
        self._local_docker_registry = None

    def __enter__(self):
        registry_port = find_free_ports(1)[0]
        registry_container_name = self._name.replace("/", "_") + "_registry"
        with ContextDockerClient() as docker_client:
            logging.debug("Start pull of registry:2")
            docker_client.images.pull(repository="registry", tag="2")
            logging.debug(f"Start container of {registry_container_name}")
            try:
                docker_client.containers.get(registry_container_name).remove(force=True)
            except:
                pass
            registry_container = docker_client.containers.run(
                image="registry:2",
                name=registry_container_name,
                ports={5000: registry_port},
                detach=True,
            )
            time.sleep(10)
            logging.debug(f"Finished start container of {registry_container_name}")
            self._local_docker_registry = LocalDockerRegistry(
                self._name, registry_container, registry_port
            )
            return self._local_docker_registry

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if self._local_docker_registry is not None:
            remove_docker_container(
                [self._local_docker_registry._registry_container.id]
            )
