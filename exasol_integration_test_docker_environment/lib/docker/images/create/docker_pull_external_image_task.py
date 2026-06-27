import luigi

from exasol_integration_test_docker_environment.lib.base.docker_base_task import (
    DockerBaseTask,
)
from exasol_integration_test_docker_environment.lib.docker.images.create.utils.docker_image_target import (
    DockerImageTarget,
)
from exasol_integration_test_docker_environment.lib.models.config.docker_config import (
    source_docker_repository_config,
)


class DockerPullExternalImageTask(DockerBaseTask):
    image_reference: str = luigi.Parameter()

    def run_task(self) -> None:
        if self._is_locally_available():
            self.logger.info(
                "Skip pull of docker image %s because it already exists locally",
                self.image_reference,
            )
            self.return_object(self.image_reference)
            return
        self.logger.info("Try to pull external docker image %s", self.image_reference)
        auth_config = self._get_auth_config()
        repository, tag = _split_image_reference(self.image_reference)
        with self._get_docker_client() as docker_client:
            docker_client.images.pull(
                repository=repository, tag=tag, auth_config=auth_config
            )
        self.return_object(self.image_reference)

    def _is_locally_available(self) -> bool:
        image_target = DockerImageTarget(*_split_image_reference(self.image_reference))
        return image_target.exists()

    def _get_auth_config(self) -> dict[str, str] | None:
        repository_config = source_docker_repository_config()
        if (
            repository_config.username is not None
            and repository_config.password is not None
        ):
            return {
                "username": repository_config.username,
                "password": repository_config.password,
            }
        return None


def _split_image_reference(image_reference: str) -> tuple[str, str]:
    if "@" in image_reference:
        repository, digest = image_reference.rsplit("@", 1)
        return repository, digest
    if ":" in image_reference.rsplit("/", 1)[-1]:
        repository, tag = image_reference.rsplit(":", 1)
        return repository, tag
    return image_reference, "latest"
