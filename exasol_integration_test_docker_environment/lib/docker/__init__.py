import docker

from exasol_integration_test_docker_environment.lib.config.docker_config import (
    source_docker_repository_config,
    target_docker_repository_config,
)


class ContextDockerClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self._client = None

    def __enter__(self):

        self._client = docker.from_env(**self.kwargs)
        self.login(self._client, source_docker_repository_config())
        self.login(self._client, target_docker_repository_config())
        return self._client

    def login(self, client: docker.client.DockerClient, docker_repository_config):
        if (
            docker_repository_config.username is not None
            and docker_repository_config.password is not None
        ):
            client.login(
                username=docker_repository_config.username,
                password=docker_repository_config.password,
            )

    def __exit__(self, type_, value, traceback):
        if self._client is not None:
            self._client.close()
        self._client = None
