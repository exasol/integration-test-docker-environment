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
from exasol_integration_test_docker_environment.lib.config.docker_config import (
    target_docker_repository_config,
)
from exasol_integration_test_docker_environment.lib.docker.images.image_info import (
    ImageInfo,
    ImageState,
)
from exasol_integration_test_docker_environment.lib.docker.images.push.push_log_handler import (
    PushLogHandler,
)


class DockerPushImageBaseTask(DockerBaseTask):
    image_name = luigi.Parameter()
    force_push = luigi.BoolParameter(
        False, visibility=luigi.parameter.ParameterVisibility.HIDDEN
    )

    def register_required(self):
        task = self.get_docker_image_task()
        self._image_info_future = self.register_dependency(task)

    def get_docker_image_task(self):
        raise AbstractMethodException()

    def run_task(self):
        image_info = self.get_values_from_future(self._image_info_future)
        was_build = image_info.image_state == ImageState.WAS_BUILD.name
        if was_build or self.force_push:
            self.logger.info("Push images")
            auth_config = {
                "username": target_docker_repository_config().username,
                "password": target_docker_repository_config().password,
            }
            with self._get_docker_client() as docker_client:
                self.logger.info(
                    f"Push images to repo={image_info.get_target_complete_name()}, "
                    f"tag={image_info.get_target_complete_tag()}"
                )
                generator = docker_client.images.push(
                    repository=image_info.get_target_complete_name(),
                    tag=image_info.get_target_complete_tag(),
                    auth_config=auth_config,
                    stream=True,
                )
                self._handle_output(generator, image_info)
        self.return_object(image_info)

    def _handle_output(self, output_generator, image_info: ImageInfo):
        log_file_path = Path(self.get_log_path(), "push.log")
        with PushLogHandler(log_file_path, self.logger, image_info) as log_hanlder:
            still_running_logger = StillRunningLogger(
                self.logger, "push image %s" % image_info.get_target_complete_name()
            )
            for log_line in output_generator:
                still_running_logger.log()
                log_hanlder.handle_log_lines(log_line)
