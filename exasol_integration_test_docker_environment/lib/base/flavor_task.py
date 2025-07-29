from pathlib import Path
from typing import (
    Any,
)

import luigi

from exasol_integration_test_docker_environment.lib.base.base_task import BaseTaskType
from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import (
    DependencyLoggerBaseTask,
)
from exasol_integration_test_docker_environment.lib.base.docker_base_task import (
    DockerBaseTask,
)


class FlavorsBaseTask(DependencyLoggerBaseTask):
    flavor_paths: tuple[str] = luigi.ListParameter()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for flavor_path in self.flavor_paths:
            if not Path(flavor_path).is_dir():
                raise OSError("Flavor path %s not a directory." % flavor_path)

    def create_tasks_for_flavors_with_common_params(
        self, cls, **kwargs
    ) -> dict[str, Any]:
        return {
            flavor_path: self._create_task_with_common_params(cls, flavor_path, kwargs)
            for flavor_path in self.flavor_paths
        }

    def _create_task_with_common_params(
        self, cls: type[BaseTaskType], flavor_path, kwargs
    ) -> BaseTaskType:
        params = {**kwargs, "flavor_path": flavor_path}
        task = self.create_child_task_with_common_params(cls, **params)
        return task


class FlavorBaseTask(DockerBaseTask):
    flavor_path: str = luigi.Parameter()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if not Path(self.flavor_path).is_dir():
            raise OSError("Flavor path %s not a directory." % self.flavor_path)

    def get_flavor_name(self) -> str:
        path = Path(self.flavor_path)
        flavor_name = path.name
        return flavor_name
