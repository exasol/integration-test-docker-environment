import re
import time
import traceback
from test.matchers import regex_matcher

import pytest
from joblib.testing import fixture

from exasol_integration_test_docker_environment.lib.models.api_errors import (
    TaskFailures,
    TaskRuntimeError,
)
from exasol_integration_test_docker_environment.lib.base.run_task import (
    generate_root_task,
    run_task,
)
from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import (
    DependencyLoggerBaseTask,
)


class CompositeFailingTask(DependencyLoggerBaseTask):

    def register_required(self):
        self.dependencies = self.register_dependencies(
            [self.create_child_task(FailingTask1), self.create_child_task(FailingTask2)]
        )
        return self.dependencies

    def run_task(self):
        pass


class FailingTask1(DependencyLoggerBaseTask):

    def run_task(self):
        # The sleep is needed to garantuee that both FailingTasks are started before one fails,
        # because otherwise the other one won't be started
        time.sleep(0.1)
        raise RuntimeError(f"Error in {self.__class__.__name__} occurred.")


class FailingTask2(DependencyLoggerBaseTask):

    def run_task(self):
        # The sleep is needed to garantuee that both FailingTasks are started before one fails,
        # because otherwise the other one won't be started
        time.sleep(0.1)
        raise RuntimeError(f"Error in {self.__class__.__name__} occurred.")


class SingleFailingTask(DependencyLoggerBaseTask):

    def run_task(self):
        raise RuntimeError(f"Error in {self.__class__.__name__} occurred.")


class TestSingleTaskFailure:

    @fixture(scope="class")
    def exception_from_sut(self) -> TaskRuntimeError:
        def task_creator():
            return generate_root_task(task_class=SingleFailingTask)

        with pytest.raises(
            TaskRuntimeError,
            match=r"Task SingleFailingTask.* \(or any of it's subtasks\) failed\.",
        ) as raises:
            run_task(task_creator=task_creator, workers=3)
        return raises.value

    @fixture
    def formatted_cause(self, exception_from_sut):
        cause = exception_from_sut.__cause__
        formatted_cause = "".join(
            traceback.format_exception(type(cause), cause, cause.__traceback__)
        )
        return formatted_cause

    def test_cause_is_task_failures_instance(self, exception_from_sut):
        cause = exception_from_sut.__cause__
        assert isinstance(cause, TaskFailures)

    def test_tasks_failures(self, formatted_cause):
        assert formatted_cause == regex_matcher(
            ".*Following task failures were caught during the execution:"
        )

    def test_task_in_list_of_failures(self, formatted_cause):
        assert formatted_cause == regex_matcher(r".*- SingleFailingTask.*:", re.DOTALL)

    def test_task_error(self, formatted_cause):
        assert formatted_cause == regex_matcher(
            r".*RuntimeError: Error in SingleFailingTask occurred\..*", re.DOTALL
        )


class TestMultipleTaskFailure:

    @fixture(scope="class")
    def exception_from_sut(self) -> TaskRuntimeError:
        def task_creator():
            return generate_root_task(task_class=CompositeFailingTask)

        with pytest.raises(
            TaskRuntimeError,
            match=r"Task CompositeFailingTask.* \(or any of it's subtasks\) failed\.",
        ) as raises:
            run_task(task_creator=task_creator, workers=3)
        return raises.value

    @fixture
    def formatted_cause(self, exception_from_sut):
        cause = exception_from_sut.__cause__
        formatted_cause = "".join(
            traceback.format_exception(type(cause), cause, cause.__traceback__)
        )
        return formatted_cause

    def test_cause_is_task_failures_instance(self, exception_from_sut):
        cause = exception_from_sut.__cause__
        assert isinstance(cause, TaskFailures)

    def test_tasks_failures(self, formatted_cause):
        assert formatted_cause == regex_matcher(
            ".*Following task failures were caught during the execution:"
        )

    def test_sub_task1_in_list_of_failures(self, formatted_cause):
        assert formatted_cause == regex_matcher(r".*- FailingTask1.*:", re.DOTALL)

    def test_sub_task2_in_list_of_failures(self, formatted_cause):
        assert formatted_cause == regex_matcher(r".*- FailingTask2.*:", re.DOTALL)

    def test_sub_task1_error(self, formatted_cause):
        assert formatted_cause == regex_matcher(
            r".*RuntimeError: Error in FailingTask1 occurred\..*", re.DOTALL
        )

    def test_sub_task2_error(self, formatted_cause):
        assert formatted_cause == regex_matcher(
            r".*RuntimeError: Error in FailingTask2 occurred\..*", re.DOTALL
        )
