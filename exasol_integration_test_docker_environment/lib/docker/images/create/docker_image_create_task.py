import copy
import importlib

import luigi

from exasol_integration_test_docker_environment.lib.base.docker_base_task import (
    DockerBaseTask,
)
from exasol_integration_test_docker_environment.lib.base.json_pickle_parameter import (
    JsonPickleParameter,
)
from exasol_integration_test_docker_environment.lib.docker.images.create.docker_image_build_task import (
    DockerBuildImageTask,
)
from exasol_integration_test_docker_environment.lib.docker.images.create.docker_image_load_task import (
    DockerLoadImageTask,
)
from exasol_integration_test_docker_environment.lib.docker.images.create.docker_image_pull_task import (
    DockerPullImageTask,
)
from exasol_integration_test_docker_environment.lib.docker.images.image_info import (
    ImageInfo,
    ImageState,
)
from exasol_integration_test_docker_environment.lib.docker.images.required_task_info import (
    RequiredTaskInfo,
    RequiredTaskInfoDict,
)


class DockerCreateImageTask(DockerBaseTask):
    image_name: str = luigi.Parameter()  # type: ignore
    # ParameterVisibility needs to be hidden instead of private, because otherwise a MissingParameter gets thrown
    image_info: ImageInfo = JsonPickleParameter(
        ImageInfo,
        visibility=luigi.parameter.ParameterVisibility.HIDDEN,
        significant=True,
    )  # type: ignore

    def run_task(self):
        new_image_info = yield from self.build(self.image_info)
        self.return_object(new_image_info)

    def build(self, image_info: ImageInfo):
        if image_info.image_state == ImageState.NEEDS_TO_BE_BUILD.name:
            task = self.create_child_task(
                DockerBuildImageTask, image_name=self.image_name, image_info=image_info
            )
            yield from self.run_dependencies(task)
            image_info.image_state = ImageState.WAS_BUILD.name  # TODO clone and change
            return image_info
        elif image_info.image_state == ImageState.CAN_BE_LOADED.name:
            task = self.create_child_task(
                DockerLoadImageTask, image_name=self.image_name, image_info=image_info
            )
            yield from self.run_dependencies(task)
            image_info.image_state = ImageState.WAS_LOADED.name
            return image_info
        elif image_info.image_state == ImageState.REMOTE_AVAILABLE.name:
            task = self.create_child_task(
                DockerPullImageTask, image_name=self.image_name, image_info=image_info
            )
            yield from self.run_dependencies(task)
            image_info.image_state = ImageState.WAS_PULLED.name
            return image_info
        elif image_info.image_state == ImageState.TARGET_LOCALLY_AVAILABLE.name:
            image_info.image_state = ImageState.USED_LOCAL.name
            return image_info
        elif image_info.image_state == ImageState.SOURCE_LOCALLY_AVAILABLE.name:
            image_info.image_state = ImageState.WAS_TAGED.name
            self.rename_source_image_to_target_image(image_info)
            return image_info
        else:
            raise Exception(
                "Task %s: Image state %s not supported for image %s",
                self.task_id,
                image_info.image_state,
                image_info.get_target_complete_name(),
            )

    def rename_source_image_to_target_image(self, image_info):
        with self._get_docker_client() as docker_client:
            docker_client.images.get(image_info.get_source_complete_name()).tag(
                repository=image_info.target_repository_name,
                tag=image_info.get_target_complete_tag(),
            )


class DockerCreateImageTaskWithDeps(DockerCreateImageTask):
    # ParameterVisibility needs to be hidden instead of private, because otherwise a MissingParameter gets thrown
    required_task_infos: RequiredTaskInfoDict = JsonPickleParameter(
        RequiredTaskInfoDict,
        visibility=luigi.parameter.ParameterVisibility.HIDDEN,
        significant=True,
    )  # type: ignore

    def register_required(self):
        self.required_tasks = {
            key: self.create_required_task(required_task_info)
            for key, required_task_info in self.required_task_infos.infos.items()
        }
        self.futures = self.register_dependencies(self.required_tasks)

    def create_required_task(
        self, required_task_info: RequiredTaskInfo
    ) -> DockerCreateImageTask:
        module = importlib.import_module(required_task_info.module_name)
        class_ = getattr(module, required_task_info.class_name)
        instance = self.create_child_task(class_, **required_task_info.params)
        return instance

    def run_task(self):
        image_infos = self.get_values_from_futures(self.futures)
        image_info = copy.copy(self.image_info)
        image_info.depends_on_images = image_infos
        new_image_info = yield from self.build(image_info)
        self.return_object(new_image_info)
