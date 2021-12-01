import shutil
import unittest

import luigi
from luigi import BoolParameter, IntParameter

from exasol_integration_test_docker_environment.cli.common import generate_root_task
from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import DependencyLoggerBaseTask

TestBaseTask = DependencyLoggerBaseTask


class TestTaskBase(TestBaseTask):
    different_grandchild = BoolParameter()
    use_dynamic_dependency = BoolParameter()

    def _build_child_task(self, use_dynamic_dependency):
        index_for_grandchild = 0
        child_a = self.create_child_task(task_class=TestTaskChildA,
                                         index_for_grandchild=index_for_grandchild,
                                         use_dynamic_dependency=use_dynamic_dependency)
        if self.different_grandchild:
            index_for_grandchild = 1
        child_b = self.create_child_task(task_class=TestTaskChildB,
                                         index_for_grandchild=index_for_grandchild,
                                         use_dynamic_dependency=use_dynamic_dependency)
        return child_a, child_b

    def register_required(self):
        if not self.use_dynamic_dependency:
            child_a, child_b = self._build_child_task(False)
            self.child_tasks = self.register_dependencies([child_a, child_b])

    def run_task(self):
        if self.use_dynamic_dependency:
            child_a, child_b = self._build_child_task(True)
            yield from self.run_dependencies([child_a, child_b])


class TestTaskChildA(TestBaseTask):
    index_for_grandchild = IntParameter()
    use_dynamic_dependency = BoolParameter()

    def register_required(self):
        if not self.use_dynamic_dependency:
            grandchild = self.create_child_task(task_class=TestTaskGrandchild,
                                                index_for_grandchild=self.index_for_grandchild)
            self.register_dependency(grandchild)

    def run_task(self):
        if self.use_dynamic_dependency:
            grandchild = self.create_child_task(task_class=TestTaskGrandchild,
                                                index_for_grandchild=self.index_for_grandchild)
            yield from self.run_dependencies(grandchild)

    def cleanup_task(self, success: bool):
        pass


class TestTaskChildB(TestBaseTask):
    index_for_grandchild = IntParameter()
    use_dynamic_dependency = BoolParameter()

    def register_required(self):
        if not self.use_dynamic_dependency:
            grandchild = self.create_child_task(task_class=TestTaskGrandchild,
                                                index_for_grandchild=self.index_for_grandchild)
            self.register_dependency(grandchild)

    def run_task(self):
        if self.use_dynamic_dependency:
            grandchild = self.create_child_task(task_class=TestTaskGrandchild,
                                                index_for_grandchild=self.index_for_grandchild)
            yield from self.run_dependencies(grandchild)

    def cleanup_task(self, success: bool):
        pass


global_counter = 0


class TestTaskGrandchild(TestBaseTask):
    index_for_grandchild = IntParameter()

    def run_task(self):
        pass

    def cleanup_task(self, success: bool):
        global global_counter
        global_counter = global_counter + 1


class BaseTaskCleanupTest(unittest.TestCase):

    def _run_it(self, different_grandchild, use_dynamic_dependency, expected_result):
        global global_counter
        global_counter = 0
        task = generate_root_task(task_class=TestTaskBase,
                                  different_grandchild=different_grandchild,
                                  use_dynamic_dependency=use_dynamic_dependency)
        try:
            luigi.build([task], workers=3, local_scheduler=True, log_level="INFO")
            task.cleanup(success=True)
        finally:
            if task._get_tmp_path_for_job().exists():
                shutil.rmtree(str(task._get_tmp_path_for_job()))
        self.assertEqual(global_counter, expected_result, "number of Cleanups not matching")

    def test_cleanup_of_grandchildren_called_only_once(self):
        """
        Test that creating the same grandchild task by two different parent tasks, will invoke cleanup of grandchild
        task only once! Luigi takes care of invoking run only once, we take care to invoke cleanup() only once.
        """
        self._run_it(different_grandchild=False, use_dynamic_dependency=False, expected_result=1)

    def test_cleanup_of_grandchildren_called_twice(self):
        """
        Test that creating grandchild task with different parameters by two different parent tasks,
        will invoke cleanup of grandchild twice.
        """
        self._run_it(different_grandchild=True, use_dynamic_dependency=False, expected_result=2)

    def test_cleanup_of_grandchildren_called_only_once_dynamic(self):
        """
        Test that creating the same grandchild task by two different parent tasks, will invoke cleanup of grandchild
        task only once! Luigi takes care of invoking run only once, we take care to invoke cleanup() only once.
        In this test all child tasks are created dynamically.
        """
        self._run_it(different_grandchild=False, use_dynamic_dependency=True, expected_result=1)

    def test_cleanup_of_grandchildren_called_twice_dynamic(self):
        """
        Test that creating grandchild task with different parameters by two different parent tasks,
        will invoke cleanup of grandchild twice.
        In this test all child tasks are created dynamically.
        """
        self._run_it(different_grandchild=True, use_dynamic_dependency=True, expected_result=2)


if __name__ == '__main__':
    unittest.main()
