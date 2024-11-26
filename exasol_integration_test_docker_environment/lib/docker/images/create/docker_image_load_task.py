from pathlib import Path

from exasol_integration_test_docker_environment.lib.config.build_config import (
    build_config,
)
from exasol_integration_test_docker_environment.lib.docker.images.create.docker_image_creator_base_task import (
    DockerImageCreatorBaseTask,
)


class DockerLoadImageTask(DockerImageCreatorBaseTask):

    def run_task(self):
        image_archive_path = Path(build_config().cache_directory).joinpath(
            self.image_info.get_source_complete_name() + ".tar"
        )
        self.logger.info(
            "Try to load docker image %s from %s",
            self.image_info.get_source_complete_name(),
            image_archive_path,
        )
        with self._get_docker_client() as docker_client:
            with image_archive_path.open("rb") as f:
                docker_client.images.load(f)
            docker_client.images.get(self.image_info.get_source_complete_name()).tag(
                repository=self.image_info.target_repository_name,
                tag=self.image_info.get_target_complete_tag(),
            )
