from __future__ import annotations

from exasol_integration_test_docker_environment.lib.base.ray_base_task import (
    RayBaseTask,
)


class RayTaskWithReturn(RayBaseTask):
    x: str

    def run_task(self):
        self.return_object(f"{self.x}-123")


class ParameterUnderTest:
    test_parameter: str


class CommonParameterRootTask(RayBaseTask, ParameterUnderTest):

    def register_required(self):
        task8 = self.create_child_task_with_common_params(
            task_class=CommonParameterChildTask, new_parameter="new"
        )
        self.task8_future = self.register_dependency(task8)

    def run_task(self):
        pass


class CommonParameterChildTask(RayBaseTask, ParameterUnderTest):
    new_parameter: str

    def run_task(self):
        pass


class DependencyRootTask(RayBaseTask):
    def register_required(self):
        self.task2 = self.register_dependency(
            self.create_child_task(task_class=DependencyStaticChildTask)
        )

    def run_task(self):
        self.logger.info("RUN")
        self.logger.info(f"task2 {self.task2.get_output()}")
        tasks_3 = yield from self.run_dependencies(
            {
                "1": DependencyDynamicChildTask(input_param="e", job_id=self.job_id),
                "2": DependencyDynamicChildTask(input_param="d", job_id=self.job_id),
            }
        )
        self.logger.info(f"""task3_1 {tasks_3["1"].get_output()}""")
        self.logger.info(f"""task3_2 {tasks_3["2"].get_output()}""")


class DependencyStaticChildTask(RayBaseTask):

    def run_task(self):
        self.logger.info("RUN")
        self.return_object([1, 2, 3, 4])


class DependencyDynamicChildTask(RayBaseTask):
    input_param: str

    def run_task(self):
        self.logger.info(f"RUN {self.input_param}")
        self.return_object(object=["a", "b", self.input_param])
