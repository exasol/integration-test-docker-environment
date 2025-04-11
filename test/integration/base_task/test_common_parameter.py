import luigi
from luigi import Config, Parameter

from exasol_integration_test_docker_environment.lib.base.run_task import generate_root_task
from test.integration.base_task.base_task import TestBaseTask


class TestParameter(Config):
    test_parameter = Parameter()


class RootTestTask(TestBaseTask, TestParameter):

    def register_required(self):
        task8 = self.create_child_task_with_common_params(
            task_class=ChildTaskWithParameter, new_parameter="new"
        )
        self.task8_future = self.register_dependency(task8)

    def run_task(self):
        pass


class ChildTaskWithParameter(TestBaseTask, TestParameter):
    new_parameter = Parameter()

    def run_task(self):
        pass


def test_common_parameter(luigi_output):
    task = generate_root_task(task_class=RootTestTask, test_parameter="input")
    result = luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
    assert result
