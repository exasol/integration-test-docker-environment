import shutil
import tempfile
from pathlib import Path

from exasol_integration_test_docker_environment.lib.base.still_running_logger import (
    StillRunningLogger,
)
from exasol_integration_test_docker_environment.lib.config.build_config import (
    build_config,
)
from exasol_integration_test_docker_environment.lib.config.docker_config import (
    docker_build_arguments,
)
from exasol_integration_test_docker_environment.lib.docker.images.create.docker_image_creator_base_task import (
    DockerImageCreatorBaseTask,
)
from exasol_integration_test_docker_environment.lib.docker.images.create.utils.build_context_creator import (
    BuildContextCreator,
)
from exasol_integration_test_docker_environment.lib.docker.images.create.utils.build_log_handler import (
    BuildLogHandler,
)
from exasol_integration_test_docker_environment.lib.docker.images.image_info import (
    ImageInfo,
)


class DockerBuildImageTask(DockerImageCreatorBaseTask):

    def run_task(self):
        self.logger.info(
            "Build docker image %s, log file can be found here %s",
            self.image_info.get_target_complete_name(),
            self.get_log_path(),
        )
        temp_directory = tempfile.mkdtemp(
            prefix="script_language_container_tmp_dir",
            dir=build_config().temporary_base_directory,
        )
        try:
            image_description = self.image_info.image_description
            build_context_creator = BuildContextCreator(
                temp_directory, self.image_info, self.get_log_path()
            )
            build_context_creator.prepare_build_context_to_temp_dir()
            with self._get_docker_client() as docker_client:
                output_generator = docker_client.api.build(
                    path=temp_directory,
                    nocache=self.no_cache,
                    tag=self.image_info.get_target_complete_name(),
                    rm=True,
                    buildargs=dict(
                        **image_description.transparent_build_arguments,
                        **image_description.image_changing_build_arguments,
                        **docker_build_arguments().secret
                    ),
                )
                self._handle_output(output_generator, self.image_info)
        finally:
            shutil.rmtree(temp_directory)

    def _handle_output(self, output_generator, image_info: ImageInfo):
        log_file_path = Path(self.get_log_path(), "docker-build.log")
        with BuildLogHandler(log_file_path, self.logger, image_info) as log_handler:
            still_running_logger = StillRunningLogger(
                self.logger, "build image %s" % image_info.get_target_complete_name()
            )
            for log_line in output_generator:
                still_running_logger.log()
                log_handler.handle_log_lines(log_line)
