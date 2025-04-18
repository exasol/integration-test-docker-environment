import time
from test.integration.base_task.base_task import BaseTestTask

import luigi
import pytest

from exasol_integration_test_docker_environment.lib.base.json_pickle_parameter import (
    JsonPickleParameter,
)
from exasol_integration_test_docker_environment.lib.base.run_task import (
    generate_root_task,
)


class Data1:
    pass


class Data:
    def __init__(self, a1: int, a2: str):
        self.a2 = a2
        self.a1 = a1

    def __repr__(self):
        return str(self.__dict__)


class RootTestTaskSuccess(BaseTestTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def register_required(self):
        inputs = [Data(i, f"{i}") for i in range(2)]
        tasks = [
            self.create_child_task(
                task_class=ChildTaskWithJsonPickleInput, parameter_1=input
            )
            for input in inputs
        ]
        self.register_dependencies(tasks)

    def run_task(self):
        yield from self.run_dependencies(
            self.create_child_task(
                task_class=ChildTaskWithJsonPickleInput, parameter_1=Data(3, "3")
            )
        )


class ChildTaskWithJsonPickleInput(BaseTestTask):
    parameter_1 = JsonPickleParameter(Data)

    def run_task(self):
        time.sleep(1)
        print(self.parameter_1)


class RootTestTaskFail(BaseTestTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def register_required(self):
        pass

    def run_task(self):
        yield from self.run_dependencies(
            self.create_child_task(
                task_class=ChildTaskWithJsonPickleInput, parameter_1=Data1()
            )
        )


def test_json_pickle_parameter_success(luigi_output):
    """
    Test the successful execution of tasks using JsonPickleParameter.

    This test ensures that valid Data objects are correctly serialized
    and deserialized when passed as parameters to child tasks.
    """
    task = generate_root_task(task_class=RootTestTaskSuccess)
    result = luigi.build([task], workers=3, local_scheduler=True, log_level="INFO")
    assert result


def test_json_pickle_parameter_fail(luigi_output):
    """
    Test the failure scenario when using JsonPickleParameter with invalid input.

    This test ensures that an exception is raised when an unsupported input
    type is used with JsonPickleParameter.
    """
    task = generate_root_task(task_class=RootTestTaskFail)
    with pytest.raises(Exception):
        luigi.build([task], workers=3, local_scheduler=True, log_level="INFO")
