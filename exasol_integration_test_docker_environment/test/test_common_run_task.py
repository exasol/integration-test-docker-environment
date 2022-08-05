import subprocess
import unittest
from pathlib import Path


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

    def test_return_value(self):
        self._execute_in_new_process(target="run_test_return_value")


if __name__ == '__main__':
    unittest.main()
