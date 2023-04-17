import os
import sys
import tempfile
from pathlib import Path

import luigi

from exasol_integration_test_docker_environment.lib.api.common import generate_root_task, run_task
from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import DependencyLoggerBaseTask
from exasol_integration_test_docker_environment.lib.base.luigi_log_config import LOG_ENV_VARIABLE_NAME, get_log_path


class TestTask(DependencyLoggerBaseTask):
    x = luigi.Parameter()

    def run_task(self):
        self.logger.info(f"Logging: {self.x}")
        self.return_object(self.job_id)


def run_simple_tasks() -> None:
    NUMBER_TASK = 5
    task_id_generator = (x for x in range(NUMBER_TASK))

    def create_task():
        return generate_root_task(task_class=TestTask, x=f"{next(task_id_generator)}")

    for i in range(NUMBER_TASK):
        jobid = run_task(create_task, workers=5, task_dependencies_dot_file=None, use_job_specific_log_file=True)
        log_path = get_log_path(jobid)
        assert log_path.exists()

        with open(log_path, "r") as f:
            log_content = f.read()
            assert f"Logging: {i}" in log_content


def run_test_same_logging_file() -> None:
    """
    Integration test which verifies that re-using the same logging for multiple tasks works as expected,
    using the default log path
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        run_simple_tasks()


def run_test_same_logging_file_env_log_path() -> None:
    """
    Integration test which verifies that re-using the same logging for multiple tasks works as expected,
    using a custom log path
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        log_path = Path(temp_dir) / "main.log"
        os.environ[LOG_ENV_VARIABLE_NAME] = str(log_path)
        run_simple_tasks()


def run_test_different_logging_file() -> None:
    """
    Integration test which verifies that changing the log path from one invocation of run_task to the next will work
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        task_creator = lambda: generate_root_task(task_class=TestTask, x="Test")

        use_specific_log_file(task_creator, temp_dir, "first")

        use_specific_log_file(task_creator, temp_dir, "second")


def use_specific_log_file(task_creator, temp_dir, test_name):
    log_path = Path(temp_dir) / (test_name + ".log")
    os.environ[LOG_ENV_VARIABLE_NAME] = str(log_path)
    jobid = run_task(task_creator, workers=5, task_dependencies_dot_file=None, use_job_specific_log_file=True)
    assert log_path.exists()
    with open(log_path, "r") as f:
        log_content = f.read()
        assert f"Logging: Test" in log_content


if __name__ == '__main__':
    test_type = sys.argv[1]

    dispatcher = {
        "run_test_different_logging_file": run_test_different_logging_file,
        "run_test_same_logging_file_env_log_path": run_test_same_logging_file_env_log_path,
        "run_test_same_logging_file": run_test_same_logging_file,
    }
    try:
        dispatcher[test_type]()
    except KeyError as e:
        raise ValueError("Unknown Test argument") from e
