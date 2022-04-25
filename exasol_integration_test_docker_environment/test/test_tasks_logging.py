import os
import tempfile
import unittest
from pathlib import Path
from click.testing import CliRunner

import luigi

from exasol_integration_test_docker_environment.cli.commands.build_test_container import build_test_container
from exasol_integration_test_docker_environment.cli.common import generate_root_task, run_task
from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import DependencyLoggerBaseTask


class TestTask(DependencyLoggerBaseTask):
    x = luigi.Parameter()

    def run(self):
        self.logger.info(f"Logging: {self.x}")


class TasksWithSameLoggingFile(unittest.TestCase):

    def test_same_logging_file(self):
        """
        Integration test which verifies that re-using the same logging for multiple tasks works as expected.
        """
        NUMBER_TASK = 5
        task_id_generator = (x for x in range(NUMBER_TASK))

        def task_creator():
            task = generate_root_task(task_class=TestTask, x=f"{next(task_id_generator)}")
            return task

        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            for i in range(NUMBER_TASK):
                success, task = run_task(task_creator, workers=5, task_dependencies_dot_file=None)
                self.assertTrue(success)

            log_path = Path(temp_dir) / ".build_output" / "jobs" / "logs" / "main.log"
            print(log_path)
            assert log_path.exists()

            with open(log_path, "r") as f:
                log_content = f.read()
                for i in range(NUMBER_TASK):
                    self.assertIn(f"Logging: {i}",  log_content)

    # def test_different_output_directory_raises_exception(self):
    #
    #     with tempfile.TemporaryDirectory() as temp_dir:
    #         cli_runner = CliRunner()
    #         result = cli_runner.invoke(build_test_container, f"--output-directory {temp_dir}/output_1")
    #         assert result.exit_code == 0
    #         cli_runner.invoke(build_test_container, f"--output-directory {temp_dir}/output_2")
    #         assert result.exit_code == 0


if __name__ == '__main__':
    unittest.main()
