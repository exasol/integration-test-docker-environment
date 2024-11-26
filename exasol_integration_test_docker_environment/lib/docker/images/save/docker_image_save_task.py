import importlib

import luigi

from exasol_integration_test_docker_environment.lib.base.json_pickle_parameter import (
    JsonPickleParameter,
)
from exasol_integration_test_docker_environment.lib.docker.images.required_task_info import (
    RequiredTaskInfo,
)
from exasol_integration_test_docker_environment.lib.docker.images.save.docker_image_save_base_task import (
    DockerSaveImageBaseTask,
)


class DockerSaveImageTask(DockerSaveImageBaseTask):
    # We need to create the DockerCreateImageTask for DockerSaveImageTask dynamically,
    # because we want to save as soon as possible after an image was build and
    # don't want to wait for the save finishing before starting to build depended images,
    # but we also need to create a DockerSaveImageTask for each DockerCreateImageTask of a goal

    required_task_info: RequiredTaskInfo = JsonPickleParameter(
        RequiredTaskInfo,
        visibility=luigi.parameter.ParameterVisibility.HIDDEN,
        significant=True,
    )  # type: ignore

    def get_docker_image_task(self):
        module = importlib.import_module(self.required_task_info.module_name)
        class_ = getattr(module, self.required_task_info.class_name)
        instance = self.create_child_task(class_, **self.required_task_info.params)
        return instance
