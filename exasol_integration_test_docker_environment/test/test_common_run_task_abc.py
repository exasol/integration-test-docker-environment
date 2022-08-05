import tempfile
import unittest

import luigi

from exasol_integration_test_docker_environment.lib.api.common import generate_root_task, run_task
from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import DependencyLoggerBaseTask


class TestTaskWithReturn(DependencyLoggerBaseTask):
    x = luigi.Parameter()

    def run_task(self):
        self.return_object(f"{self.x}-123")


class CommonRunTaskTest(unittest.TestCase):

    def test_return_value(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            task_creator = lambda: generate_root_task(task_class=TestTaskWithReturn, x="Test")

            return_value = run_task(task_creator, workers=5, task_dependencies_dot_file=None)
            assert return_value == "Test-123"


if __name__ == '__main__':
    unittest.main()
