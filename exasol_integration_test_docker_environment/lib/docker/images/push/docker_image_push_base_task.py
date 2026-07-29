from pathlib import Path

import luigi

from exasol_integration_test_docker_environment.abstract_method_exception import (
    AbstractMethodException,
)
from exasol_integration_test_docker_environment.lib.base.docker_base_task import (
    DockerBaseTask,
)
from exasol_integration_test_docker_environment.lib.base.still_running_logger import (
    StillRunningLogger,
)
from exasol_integration_test_docker_environment.lib.docker.images.image_info import (
    ImageInfo,
    ImageState,
)
from exasol_integration_test_docker_environment.lib.docker.images.push.push_log_handler import (
    PushLogHandler,
)
from exasol_integration_test_docker_environment.lib.models.config.docker_config import (
    target_docker_repository_config,
)


class DockerPushImageBaseTask(DockerBaseTask):
    image_name: str = luigi.Parameter()
    force_push: bool = luigi.BoolParameter(
        default=False, visibility=luigi.parameter.ParameterVisibility.HIDDEN
    )

    def register_required(self):
        task = self.get_docker_image_task()
        self._image_info_future = self.register_dependency(task)

    def get_docker_image_task(self):
        raise AbstractMethodException()

    def run_task(self) -> None:
        image_info = self.get_values_from_future(self._image_info_future)
        was_build = image_info.image_state == ImageState.WAS_BUILD.name
        if was_build or self.force_push:
            self.logger.info("Push images")
            auth_config = {
                "username": target_docker_repository_config().username,
                "password": target_docker_repository_config().password,
            }
            with self._get_docker_client() as docker_client:
                self._push_tag(
                    docker_client,
                    image_info,
                    image_info.get_target_complete_tag(),
                    auth_config,
                )
                build_name_tag = image_info.get_target_build_name_complete_tag()
                if build_name_tag:
                    self._push_tag(
                        docker_client, image_info, build_name_tag, auth_config
                    )
        self.return_object(image_info)

    def _push_tag(self, docker_client, image_info, tag, auth_config) -> None:
        self.logger.info(
            "Push image to repo=%s, tag=%s", image_info.target_repository_name, tag
        )
        generator = docker_client.images.push(
            repository=image_info.target_repository_name,
            tag=tag,
            auth_config=auth_config,
            stream=True,
        )
        self._handle_output(generator, image_info)

    def _handle_output(self, output_generator, image_info: ImageInfo):
        log_file_path = Path(self.get_log_path(), "push.log")
        with PushLogHandler(log_file_path, self.logger, image_info) as log_hanlder:
            still_running_logger = StillRunningLogger(
                self.logger, "push image %s" % image_info.get_target_complete_name()
            )
            for log_line in output_generator:
                still_running_logger.log()
                log_hanlder.handle_log_lines(log_line)
