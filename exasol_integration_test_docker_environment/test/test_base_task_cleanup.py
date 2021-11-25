import shutil
import unittest

import luigi
from luigi import Parameter

from exasol_integration_test_docker_environment.cli.common import generate_root_task
from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import DependencyLoggerBaseTask

TestBaseTask = DependencyLoggerBaseTask


class TestTaskBase(TestBaseTask):
    def register_required(self):
        grandchild = self.create_child_task(task_class=TestTaskGrandchild)
        childA = self.create_child_task(task_class=TestTaskChild, grandchild=grandchild, index=0)
        childB = self.create_child_task(task_class=TestTaskChild, grandchild=grandchild, index=1)
        self.child_tasks = self.register_dependencies([childA, childB])

    def run_task(self):
        self.logger.info(f"GREMLING: TestTaskBase started")


class TestTaskChild(TestBaseTask):
    grandchild = Parameter()
    index = Parameter()

    def register_required(self):
        self.register_dependency(self.grandchild)

    def run_task(self):
        self.logger.info(f"GREMLING: TestTaskChild started {self.index}")

    def cleanup_task(self, success:bool):
        self.logger.info(f"GREMLING: Cleanup of TestTaskChild: {self.index}")


class TestTaskGrandchild(TestBaseTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cleanup_counter = 0

    def run_task(self):
        self.logger.info(f"GREMLING: TestTaskGrandchild started")

    def cleanup_task(self, success:bool):
        self.logger.info(f"GREMLING: Cleanup")
        self.cleanup_counter = self.cleanup_counter + 1
        if self.cleanup_counter > 1:
            raise RuntimeError("Cleanup must be called only once")


class BaseTaskCleanupTest(unittest.TestCase):

    def test_cleanup_of_grandchildren_called_only_once(self):
        task = generate_root_task(task_class=TestTaskBase)
        try:
            luigi.build([task], workers=3, local_scheduler=True, log_level="INFO")
            task.cleanup(success=True)
        finally:
            if task._get_tmp_path_for_job().exists():
                shutil.rmtree(str(task._get_tmp_path_for_job()))


if __name__ == '__main__':
    unittest.main()
