import re
import time
import traceback

import pytest

from exasol_integration_test_docker_environment.lib.api.api_errors import TaskRuntimeError, TaskFailures
from exasol_integration_test_docker_environment.lib.api.common import run_task, generate_root_task
from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import DependencyLoggerBaseTask
from test.matchers import regex_matcher


class CompositeFailingTask(DependencyLoggerBaseTask):

    def register_required(self):
        self.dependencies = self.register_dependencies(
            [self.create_child_task(FailingTask1),
             self.create_child_task(FailingTask2)]
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


def test_single_task_failure():
    def task_creator():
        return generate_root_task(task_class=SingleFailingTask)

    with pytest.raises(TaskRuntimeError,
                       match=r"Task SingleFailingTask.* \(or any of it's subtasks\) failed\.") as raises:
        run_task(task_creator=task_creator)
    cause = raises.value.__cause__
    assert isinstance(cause, TaskFailures)
    formatted_exception = "".join(traceback.format_exception(type(cause), cause, cause.__traceback__))
    assert formatted_exception.startswith(
        "exasol_integration_test_docker_environment.lib.api.api_errors.TaskFailures: Following task failures were caught during the execution:")
    assert formatted_exception == regex_matcher(".*- SingleFailingTask.*:", re.DOTALL)
    assert formatted_exception == regex_matcher(".*RuntimeError: Error in SingleFailingTask occurred\..*", re.DOTALL)


def test_multiple_task_failure():
    def task_creator():
        return generate_root_task(task_class=CompositeFailingTask)

    with pytest.raises(TaskRuntimeError,
                       match=r"Task CompositeFailingTask.* \(or any of it's subtasks\) failed\.") as raises:
        run_task(task_creator=task_creator, workers=3)
    cause = raises.value.__cause__
    assert isinstance(cause, TaskFailures)
    formatted_exception = "".join(traceback.format_exception(type(cause), cause, cause.__traceback__))
    assert formatted_exception.startswith(
        "exasol_integration_test_docker_environment.lib.api.api_errors.TaskFailures: Following task failures were caught during the execution:")
    assert formatted_exception == regex_matcher(".*- FailingTask1.*:", re.DOTALL)
    assert formatted_exception == regex_matcher(".*- FailingTask2.*:", re.DOTALL)
    assert formatted_exception == regex_matcher(".*RuntimeError: Error in FailingTask1 occurred\..*", re.DOTALL)
    assert formatted_exception == regex_matcher(".*RuntimeError: Error in FailingTask2 occurred\..*", re.DOTALL)