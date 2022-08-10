import subprocess
import unittest
from pathlib import Path

import luigi

from exasol_integration_test_docker_environment.lib.api.common import generate_root_task, run_task
from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import DependencyLoggerBaseTask


class CommonRunTaskTest(unittest.TestCase):
    """
    All tests are executed in another process as we test the logging behavior which can be configured
    only once for a process!
    Note that multiprocessing.Process() does not work as it forks the current process, and thus inherits the
    logging configuration. Hence we need to start a new process with subprocess.
    """

    def _execute_in_new_process(self, target):
        path = Path(__file__)
        args = ("python", f"{path.parent.absolute()}/test_common_run_task_subprocess.py", target)
        p = subprocess.run(args)
        p.check_returncode()

    def test_same_logging_file(self):
        self._execute_in_new_process(target="run_test_same_logging_file")

    def test_same_logging_file_custom_log_location(self):
        self._execute_in_new_process(target="run_test_same_logging_file_env_log_path")

    def test_different_logging_file_raises_error(self):
        self._execute_in_new_process(target="run_test_different_logging_file_raises_error")


class TestTaskWithReturn(DependencyLoggerBaseTask):
    x = luigi.Parameter()

    def run_task(self):
        self.return_object(f"{self.x}-123")


class ReturnValueRunTaskTest(unittest.TestCase):

    def test_return_value(self) -> None:
        """
        Integration test which verifies that the return value processing in run_task works as expected.
        """

        task_creator = lambda: generate_root_task(task_class=TestTaskWithReturn, x="Test")

        return_value = run_task(task_creator, workers=5, task_dependencies_dot_file=None)
        assert return_value == "Test-123"


if __name__ == '__main__':
    unittest.main()
