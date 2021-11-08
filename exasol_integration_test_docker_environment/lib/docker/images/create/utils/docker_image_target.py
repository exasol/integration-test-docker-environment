import docker
import luigi

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient


class DockerImageTarget(luigi.Target):
    def __init__(self, image_name: str, image_tag: str):
        self.image_name = image_name
        self.image_tag = image_tag

    def get_complete_name(self):
        return f"{self.image_name}:{self.image_tag}"

    def exists(self) -> bool:
        with ContextDockerClient() as docker_client:
            try:
                image = docker_client.images.get(self.get_complete_name())
                return True
            except docker.errors.DockerException as e:
                return False
