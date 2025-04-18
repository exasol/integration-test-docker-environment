from test.integration.base_task.base_task import BaseTestTask

import luigi
from luigi import (
    Config,
    Parameter,
)

from exasol_integration_test_docker_environment.lib.base.run_task import (
    generate_root_task,
)


class ParameterUnderTest(Config):
    test_parameter = Parameter()


class RootTestTask(BaseTestTask, ParameterUnderTest):

    def register_required(self):
        task8 = self.create_child_task_with_common_params(
            task_class=ChildTaskWithParameter, new_parameter="new"
        )
        self.task8_future = self.register_dependency(task8)

    def run_task(self):
        pass


class ChildTaskWithParameter(BaseTestTask, ParameterUnderTest):
    new_parameter = Parameter()

    def run_task(self):
        pass


def test_common_parameter(luigi_output):
    """
    Test the usage of common parameters in a Luigi-based task hierarchy.

    This test verifies that a root task (`RootTestTask`) can successfully create a child task
    (`ChildTaskWithParameter`) using shared configuration parameters defined in the `TestParameter` class.
    It ensures that:
    1. Shared parameters are correctly passed down the task hierarchy.
    2. A root task can register and manage dependencies for its child tasks.
    3. The task execution completes successfully without errors when using common parameters.

    Args:
        luigi_output: A fixture or mock object used to capture Luigi's output for validation purposes.

    Assertions:
        - The `luigi.build()` function returns `True`, indicating that all tasks were executed successfully.
    """

    task = generate_root_task(task_class=RootTestTask, test_parameter="input")
    result = luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
    assert result
