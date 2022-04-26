import os
import sys
import tempfile
from pathlib import Path

import luigi

from exasol_integration_test_docker_environment.cli.common import generate_root_task, run_task
from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import DependencyLoggerBaseTask

from exasol_integration_test_docker_environment.lib.base.luigi_log_config import LOG_ENV_VARIABLE_NAME


class TestTask(DependencyLoggerBaseTask):
    x = luigi.Parameter()

    def run(self):
        self.logger.info(f"Logging: {self.x}")


def run_simple_tasks(log_path: Path) -> None:
    NUMBER_TASK = 5
    task_id_generator = (x for x in range(NUMBER_TASK))

    def create_task():
        return generate_root_task(task_class=TestTask, x=f"{next(task_id_generator)}")

    for i in range(NUMBER_TASK):
        success, task = run_task(create_task, workers=5, task_dependencies_dot_file=None)
        assert success

    assert log_path.exists()
    with open(log_path, "r") as f:
        log_content = f.read()
        for i in range(NUMBER_TASK):
            assert f"Logging: {i}" in log_content


def run_test_same_logging_file() -> None:
    """
    Integration test which verifies that re-using the same logging for multiple tasks works as expected,
    using the default log path
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        log_path = Path(temp_dir) / ".build_output" / "jobs" / "logs" / "main.log"
        run_simple_tasks(log_path=log_path)


def run_test_same_logging_file_env_log_path() -> None:
    """
    Integration test which verifies that re-using the same logging for multiple tasks works as expected,
    using a custom log path
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        log_path = Path(temp_dir) / "main.log"
        os.environ[LOG_ENV_VARIABLE_NAME] = str(log_path)
        run_simple_tasks(log_path=log_path)


def run_test_different_logging_file_raises_error() -> None:
    """
    Integration test which verifies that changing the log path from one invocation of run_task to the next will raise
    an error.
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        task_creator = lambda: generate_root_task(task_class=TestTask, x="Test")

        success, task = run_task(task_creator, workers=5, task_dependencies_dot_file=None)
        assert success
        log_path = Path(temp_dir) / "main.log"
        os.environ[LOG_ENV_VARIABLE_NAME] = str(log_path)
        success, task = run_task(task_creator, workers=5, task_dependencies_dot_file=None)
        assert success is False


if __name__ == '__main__':
    test_type = sys.argv[1]

    dispatcher = {
        "run_test_different_logging_file_raises_error": run_test_different_logging_file_raises_error,
        "run_test_same_logging_file_env_log_path": run_test_same_logging_file_env_log_path,
        "run_test_same_logging_file": run_test_same_logging_file,
    }
    try:
        dispatcher[test_type]()
    except KeyError as e:
        raise ValueError("Unknow Test argument") from e

