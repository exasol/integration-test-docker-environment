
import luigi
from luigi import Parameter

from exasol_integration_test_docker_environment.lib.base.run_task import generate_root_task
from test.integration.base_task.base_task import TestBaseTask


class RootTestTask(TestBaseTask):
    def register_required(self):
        self.task2 = self.register_dependency(
            self.create_child_task(task_class=StaticChildTask)
        )

    def run_task(self):
        self.logger.info("RUN")
        self.logger.info(f"task2 {self.task2.get_output()}")
        tasks_3 = yield from self.run_dependencies(
            {
                "1": DynamiChildTask(input_param="e", job_id=self.job_id),
                "2": DynamiChildTask(input_param="d", job_id=self.job_id),
            }
        )
        self.logger.info(f"""task3_1 {tasks_3["1"].get_output()}""")
        self.logger.info(f"""task3_2 {tasks_3["2"].get_output()}""")


class StaticChildTask(TestBaseTask):

    def run_task(self):
        self.logger.info("RUN")
        self.return_object([1, 2, 3, 4])


class DynamiChildTask(TestBaseTask):
    input_param = Parameter()

    def run_task(self):
        self.logger.info(f"RUN {self.input_param}")
        self.return_object(object=["a", "b", self.input_param])


def test_dependency_creation(luigi_output):
    task = generate_root_task(task_class=RootTestTask)
    result = luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
    assert result
