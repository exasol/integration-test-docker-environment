from test.integration.base_task.base_task import BaseTestTask

import luigi
from luigi import (
    BoolParameter,
    IntParameter,
)

from exasol_integration_test_docker_environment.lib.base.run_task import (
    generate_root_task,
)


class RootTestTask(BaseTestTask):
    different_grandchild = BoolParameter()
    use_dynamic_dependency = BoolParameter()

    def _build_child_task(self, use_dynamic_dependency):
        index_for_grandchild = 0
        child_a = self.create_child_task(
            task_class=ChildATestTask,
            index_for_grandchild=index_for_grandchild,
            use_dynamic_dependency=use_dynamic_dependency,
        )
        if self.different_grandchild:
            index_for_grandchild = 1
        child_b = self.create_child_task(
            task_class=ChildBTestTask,
            index_for_grandchild=index_for_grandchild,
            use_dynamic_dependency=use_dynamic_dependency,
        )
        return child_a, child_b

    def register_required(self):
        if not self.use_dynamic_dependency:
            child_a, child_b = self._build_child_task(False)
            self.child_tasks = self.register_dependencies([child_a, child_b])

    def run_task(self):
        if self.use_dynamic_dependency:
            child_a, child_b = self._build_child_task(True)
            yield from self.run_dependencies([child_a, child_b])


class ChildATestTask(BaseTestTask):
    index_for_grandchild = IntParameter()
    use_dynamic_dependency = BoolParameter()

    def register_required(self):
        if not self.use_dynamic_dependency:
            grandchild = self.create_child_task(
                task_class=GrandchildTestTask,
                index_for_grandchild=self.index_for_grandchild,
            )
            self.register_dependency(grandchild)

    def run_task(self):
        if self.use_dynamic_dependency:
            grandchild = self.create_child_task(
                task_class=GrandchildTestTask,
                index_for_grandchild=self.index_for_grandchild,
            )
            yield from self.run_dependencies(grandchild)

    def cleanup_task(self, success: bool):
        pass


class ChildBTestTask(BaseTestTask):
    index_for_grandchild = IntParameter()
    use_dynamic_dependency = BoolParameter()

    def register_required(self):
        if not self.use_dynamic_dependency:
            grandchild = self.create_child_task(
                task_class=GrandchildTestTask,
                index_for_grandchild=self.index_for_grandchild,
            )
            self.register_dependency(grandchild)

    def run_task(self):
        if self.use_dynamic_dependency:
            grandchild = self.create_child_task(
                task_class=GrandchildTestTask,
                index_for_grandchild=self.index_for_grandchild,
            )
            yield from self.run_dependencies(grandchild)

    def cleanup_task(self, success: bool):
        pass


global_cleanup_counter = 0


class GrandchildTestTask(BaseTestTask):
    index_for_grandchild = IntParameter()

    def run_task(self):
        pass

    def cleanup_task(self, success: bool):
        global global_cleanup_counter
        global_cleanup_counter = global_cleanup_counter + 1


def _run_root_task(different_grandchild, use_dynamic_dependency):
    global global_cleanup_counter
    global_cleanup_counter = 0
    task = generate_root_task(
        task_class=RootTestTask,
        different_grandchild=different_grandchild,
        use_dynamic_dependency=use_dynamic_dependency,
    )
    luigi.build([task], workers=3, local_scheduler=True, log_level="INFO")
    task.cleanup(success=True)
    return global_cleanup_counter


def test_cleanup_of_grandchildren_called_only_once(luigi_output):
    """
    Test that creating the same grandchild task by two different parent tasks, will invoke cleanup of grandchild
    task only once! Luigi takes care of invoking run only once, we take care to invoke cleanup() only once.
    """
    counter = _run_root_task(different_grandchild=False, use_dynamic_dependency=False)
    assert counter == 1, "number of Cleanups not matching"


def test_cleanup_of_grandchildren_called_twice(luigi_output):
    """
    Test that creating grandchild task with different parameters by two different parent tasks,
    will invoke cleanup of grandchild twice.
    """
    counter = _run_root_task(different_grandchild=True, use_dynamic_dependency=False)
    assert counter == 2, "number of Cleanups not matching"


def test_cleanup_of_grandchildren_called_only_once_dynamic(luigi_output):
    """
    Test that creating the same grandchild task by two different parent tasks, will invoke cleanup of grandchild
    task only once! Luigi takes care of invoking run only once, we take care to invoke cleanup() only once.
    In this test all child tasks are created dynamically.
    """
    counter = _run_root_task(different_grandchild=False, use_dynamic_dependency=True)
    assert counter == 1, "number of Cleanups not matching"


def test_cleanup_of_grandchildren_called_twice_dynamic(luigi_output):
    """
    Test that creating grandchild task with different parameters by two different parent tasks,
    will invoke cleanup of grandchild twice.
    In this test all child tasks are created dynamically.
    """
    counter = _run_root_task(different_grandchild=True, use_dynamic_dependency=True)
    assert counter == 2, "number of Cleanups not matching"
