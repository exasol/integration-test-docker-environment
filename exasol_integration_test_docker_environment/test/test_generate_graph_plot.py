import os
import sys
import tempfile
import unittest
from pathlib import Path

import luigi

from exasol_integration_test_docker_environment.cli.common import generate_root_task, run_task
from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import DependencyLoggerBaseTask

from exasol_integration_test_docker_environment.lib.base.luigi_log_config import LOG_ENV_VARIABLE_NAME


class TestTask(DependencyLoggerBaseTask):
    x = luigi.Parameter()

    def register_required(self):
        self.register_dependency(self.create_child_task(task_class=TestChildTask))

    def run(self):
        pass


class TestChildTask(DependencyLoggerBaseTask):
    def run_task(self):
        pass


class BaseTaskTest(unittest.TestCase):

    def test_generate_dependency_dot_file(self):
        NUMBER_TASK = 5
        task_id_generator = (x for x in range(NUMBER_TASK))

        def create_task():
            return generate_root_task(task_class=TestTask, x=f"{next(task_id_generator)}")

        with tempfile.TemporaryDirectory() as d:
            for i in range(NUMBER_TASK):
                dot_file = Path(d) / f"dot_file_{i}.dot"
                success, task = run_task(create_task, workers=5, task_dependencies_dot_file=str(dot_file))
                assert success
                assert dot_file.exists()


if __name__ == '__main__':
    unittest.main()