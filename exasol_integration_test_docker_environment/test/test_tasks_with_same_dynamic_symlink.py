import os
import tempfile
import unittest
from pathlib import Path

import luigi

from exasol_integration_test_docker_environment.cli.common import generate_root_task, run_task
from exasol_integration_test_docker_environment.lib.base.base_task import BaseTask
from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import DependencyLoggerBaseTask
from exasol_integration_test_docker_environment.lib.base.dynamic_symlink import DynamicSymlink


class TestTask(DependencyLoggerBaseTask):
    x = luigi.Parameter()

    def run(self):
        self.logger.info(f"Logging: {self.x}")


class TasksWithSameDynamicSymlinkTest(unittest.TestCase):

    def test_same_dynamic_symlink(self):
        """
        Integration test which verifies that re-using the same DynamicSymlink object redirects luigi-log's as expected.
        """
        NUMBER_TASK = 5
        task_log_paths = list()
        task_id_generator = (x * x for x in range(NUMBER_TASK))

        def task_creator():
            task = generate_root_task(task_class=TestTask, x=f"{next(task_id_generator)}")
            task_log_paths.append(task.get_log_file())
            return task

        #with tempfile.TemporaryDirectory() as temp_dir:
        with Path("/tmp/abc") as temp_dir:
            os.chdir(temp_dir)
            log_link = DynamicSymlink("test_link")
            for i in range(NUMBER_TASK):
                success, task = run_task(task_creator, workers=5, task_dependencies_dot_file=None, log_symlink=log_link)
            for i in range(NUMBER_TASK):
                log_path = Path(task_log_paths[i])

                assert log_path.exists()
                print(f"LogPath[{i}: {log_path}")
                with open(log_path, "r") as f:
                    log_content = f.read()
                    self.assertIn(f"Logging: {i}",  log_content)


if __name__ == '__main__':
    unittest.main()
