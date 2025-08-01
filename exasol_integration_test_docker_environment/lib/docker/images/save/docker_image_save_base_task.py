import os
import pathlib
import re
from collections.abc import Generator

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

DOCKER_HUB_REGISTRY_URL_REGEX = r"^.*docker.io/"


# TODO align and extract save_path of DockerSaveImageTask and load_path of DockerLoadImageTask
class DockerSaveImageBaseTask(DockerBaseTask):
    image_name: str = luigi.Parameter()
    force_save: bool = luigi.BoolParameter(
        default=False, visibility=luigi.parameter.ParameterVisibility.HIDDEN
    )
    save_path: str = luigi.Parameter(
        visibility=luigi.parameter.ParameterVisibility.HIDDEN
    )

    def register_required(self):
        task = self.get_docker_image_task()
        self._image_info_future = self.register_dependency(task)

    def get_docker_image_task(self):
        raise AbstractMethodException()

    def run_task(self) -> None:
        image_info: ImageInfo = self.get_values_from_future(self._image_info_future)
        tag_for_save: str = self.get_tag_for_save(image_info)
        save_file_path = pathlib.Path(
            self.save_path, f"{image_info.get_target_complete_name()}.tar"
        )
        was_build = image_info.image_state == ImageState.WAS_BUILD.name
        if was_build or self.force_save or not save_file_path.exists():
            self.save_image(image_info, tag_for_save, save_file_path)
        self.return_object(image_info)

    def get_tag_for_save(self, image_info: ImageInfo):
        tag_for_save = re.sub(
            DOCKER_HUB_REGISTRY_URL_REGEX, "", image_info.get_target_complete_name()
        )
        return tag_for_save

    def save_image(
        self, image_info: ImageInfo, tag_for_save: str, save_file_path: pathlib.Path
    ):
        self.remove_save_file_if_necassary(save_file_path)
        with self._get_docker_client() as docker_client:
            image = docker_client.images.get(image_info.get_target_complete_name())
            generator = image.save(named=tag_for_save)
            self.write_image_to_file(save_file_path, image_info, generator)

    def remove_save_file_if_necassary(self, save_file_path: pathlib.Path):
        save_file_path.parent.mkdir(exist_ok=True, parents=True)
        if save_file_path.exists():
            os.remove(str(save_file_path))

    def write_image_to_file(
        self,
        save_file_path: pathlib.Path,
        image_info: ImageInfo,
        output_generator: Generator,
    ):
        self.logger.info(
            f"Saving image {image_info.get_target_complete_name()} to file {save_file_path}"
        )
        with save_file_path.open("wb") as file:
            still_running_logger = StillRunningLogger(
                self.logger, "save image %s" % image_info.get_target_complete_name()
            )
            for chunk in output_generator:
                still_running_logger.log()
                file.write(chunk)
