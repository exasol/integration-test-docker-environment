import itertools

from exasol_integration_test_docker_environment.abstract_method_exception import (
    AbstractMethodException,
)
from exasol_integration_test_docker_environment.lib.base.base_task import BaseTask
from exasol_integration_test_docker_environment.lib.docker.images.create.docker_image_create_task import (
    DockerCreateImageTask,
    DockerCreateImageTaskWithDeps,
)
from exasol_integration_test_docker_environment.lib.docker.images.required_task_info import (
    RequiredTaskInfo,
)


class TaskCreatorFromBuildTasks:

    def create_tasks_for_build_tasks(
        self, build_tasks: dict[str, DockerCreateImageTask]
    ) -> list[BaseTask]:
        tasks_per_goal = [
            self._create_tasks_for_build_task(build_task)
            for goal, build_task in build_tasks.items()
        ]
        return list(itertools.chain.from_iterable(tasks_per_goal))

    def _create_tasks_for_build_task(
        self, build_task: DockerCreateImageTask
    ) -> list[DockerCreateImageTaskWithDeps]:
        if isinstance(build_task, DockerCreateImageTaskWithDeps):
            tasks = self.create_tasks_for_build_tasks(build_task.required_tasks)
            task = self._create_task(build_task)
            return [task] + tasks
        else:
            task = self._create_task(build_task)
            return [task]

    def _create_task(self, build_task):
        required_task_info = self._create_required_task_info(build_task)
        task = self.create_task_with_required_tasks(build_task, required_task_info)
        return task

    def _create_required_task_info(self, build_task: DockerCreateImageTask):
        required_task_info = RequiredTaskInfo(
            module_name=build_task.__module__,
            class_name=build_task.__class__.__name__,
            params=build_task.param_kwargs,
        )
        return required_task_info

    def create_task_with_required_tasks(
        self, build_task, required_task_info
    ) -> BaseTask:
        raise AbstractMethodException()
