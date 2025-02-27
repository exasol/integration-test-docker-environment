from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
)

import luigi

from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import (
    DependencyLoggerBaseTask,
)
from exasol_integration_test_docker_environment.lib.base.docker_base_task import (
    DockerBaseTask,
)


class FlavorsBaseTask(DependencyLoggerBaseTask):
    flavor_paths: List[str] = luigi.ListParameter()  # type: ignore

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for flavor_path in self.flavor_paths:
            if not Path(flavor_path).is_dir():
                raise OSError("Flavor path %s not a directory." % flavor_path)

    def create_tasks_for_flavors_with_common_params(
        self, cls, **kwargs
    ) -> Dict[str, Any]:
        return {
            flavor_path: self._create_task_for_with_common_params(
                cls, flavor_path, kwargs
            )
            for flavor_path in self.flavor_paths
        }

    def _create_task_for_with_common_params(self, cls, flavor_path, kwargs):
        params = {**kwargs, "flavor_path": flavor_path}
        task = self.create_child_task_with_common_params(cls, **params)
        return task


class FlavorBaseTask(DockerBaseTask):
    flavor_path = luigi.Parameter()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not Path(self.flavor_path).is_dir():
            raise OSError("Flavor path %s not a directory." % self.flavor_path)

    def get_flavor_name(self):
        path = Path(self.flavor_path)
        flavor_name = path.name
        return flavor_name
