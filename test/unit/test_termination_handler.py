import dataclasses
import io
import re
import time
from contextlib import (
    ExitStack,
    redirect_stderr,
    redirect_stdout,
)

from exasol_integration_test_docker_environment.lib.api.run_task import generate_root_task, run_task
from test.matchers import regex_matcher

import pytest

from exasol_integration_test_docker_environment.cli.termination_handler import (
    TerminationHandler,
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


@dataclasses.dataclass
class Capture:
    err: str
    out: str


@pytest.fixture(scope="module")
def capture_output_of_test() -> Capture:
    out = io.StringIO()
    err = io.StringIO()
    with ExitStack() as stack:
        # We can't use capsys, because this is a function scope fixture,
        # but we want to execute the task only once, due to the sleep
        stack.enter_context(redirect_stdout(out))
        stack.enter_context(redirect_stderr(err))
        stack.enter_context(pytest.raises(SystemExit))
        stack.enter_context(TerminationHandler())

        def task_creator():
            return generate_root_task(task_class=CompositeFailingTask)

        run_task(task_creator=task_creator, workers=3)
    return Capture(out=out.getvalue(), err=err.getvalue())


def test_command_runtime(capture_output_of_test):
    assert capture_output_of_test.err == regex_matcher(
        "The command failed after .* s with:"
    )


def test_composite_task_failed(capture_output_of_test):
    assert capture_output_of_test.err == regex_matcher(
        r".*Task failure message: Task CompositeFailingTask.* \(or any of it's subtasks\) failed\.",
        re.DOTALL,
    )


def test_sub_tasks_failed(capture_output_of_test):
    assert capture_output_of_test.err == regex_matcher(
        r".*Following task failures were caught during the execution:", re.DOTALL
    )


def test_sub_task1_error(capture_output_of_test):
    assert capture_output_of_test.err == regex_matcher(
        r".*RuntimeError: Error in FailingTask1 occurred.", re.DOTALL
    )


def test_sub_task2_error(capture_output_of_test):
    assert capture_output_of_test.err == regex_matcher(
        r".*RuntimeError: Error in FailingTask2 occurred.", re.DOTALL
    )


def test_out_empty(capture_output_of_test):
    assert capture_output_of_test.out == ""
