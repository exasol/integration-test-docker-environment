import pytest
import os.path
import tempfile
from pathlib import Path

import luigi

from exasol_integration_test_docker_environment.lib.base.luigi_log_config import LOG_ENV_VARIABLE_NAME, get_log_path
from exasol_integration_test_docker_environment.lib.api.common import generate_root_task, run_task
from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import DependencyLoggerBaseTask
from exasol_integration_test_docker_environment.lib.config.build_config import build_config

@pytest.fixture
def set_tempdir():
    path_old = os.getcwd()
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        yield temp_dir
    os.chdir(path_old)


def default_log_path(job_id):
    return Path(build_config().output_directory) / "jobs" / job_id / "logs" / "main.log"


class TestTask_env(DependencyLoggerBaseTask):
    x = luigi.Parameter()

    def run_task(self):
        self.logger.info(f"Logging: {self.x}")
        self.return_object({"job_id": self.job_id, "parameter": self.x})


def run_n_simple_tasks(task_number):
    NUMBER_TASK = task_number
    task_id_generator = (x for x in range(NUMBER_TASK))
    tasks = []

    def create_task():
        return generate_root_task(task_class=TestTask_env, x=f"{next(task_id_generator)}")

    for j in range(NUMBER_TASK):
        output = run_task(create_task, workers=5, task_dependencies_dot_file=None, use_job_specific_log_file=True)
        jobid = output["job_id"]
        log_path = get_log_path(jobid)
        tasks.append({"jobid": jobid, "log_path": log_path, "in_parameter": output["parameter"]})
        assert log_path.exists()
        assert os.path.isfile(log_path)

    for task in tasks:
        # extra loop, so we can check if all log content exists after tasks are finished.
        # makes sure no log content got overwritten
        with open(task["log_path"], "r") as f:
            log_content = f.read()
            in_param = task['in_parameter']
            assert f"Logging: {in_param}" in log_content
    return tasks


def use_specific_log_file(task_creator, temp_dir, test_name):
    log_path = Path(temp_dir) / (test_name + ".log")
    os.environ[LOG_ENV_VARIABLE_NAME] = str(log_path)
    jobid = run_task(task_creator, workers=5, task_dependencies_dot_file=None, use_job_specific_log_file=True)
    assert log_path.exists()
    with open(log_path, "r") as f:
        log_content = f.read()
        assert f"Logging: Test" in log_content
    os.environ.pop(LOG_ENV_VARIABLE_NAME)


def test_var_not_set(set_tempdir):
    """
    Integration test which verifies that not setting the env var LOG_ENV_VARIABLE_NAME works and uses the
    default log path
    """
    tasks = run_n_simple_tasks(1)
    assert tasks[0]["log_path"] == default_log_path(tasks[0]["jobid"])


def test_var_not_set_same_logging_file(set_tempdir):
    """
    Integration test which verifies that re-using the same logging for multiple tasks works as expected,
    using the default log path
    """
    tasks = run_n_simple_tasks(5)
    for task in tasks:
        assert task["log_path"] == default_log_path(task["jobid"])


def test_custom_log_path_points_at_file(set_tempdir):
    """
    Integration test which verifies that using a custom log path for a single task works if the path points to a file
    """
    temp_dir = set_tempdir
    custom_log_path = Path(temp_dir) / "main.log"
    os.environ[LOG_ENV_VARIABLE_NAME] = str(custom_log_path)
    tasks = run_n_simple_tasks(1)
    assert tasks[0]["log_path"] == custom_log_path
    os.environ.pop(LOG_ENV_VARIABLE_NAME)


def test_preexisting_custom_log_file(set_tempdir):
    """
    Integration test which verifies that using a custom log path for a single task works if file already exists.
    """
    temp_dir = set_tempdir
    custom_log_path = Path(temp_dir) / "main.log"
    file_content = "This existing file has content."
    with open(custom_log_path, "a") as f:
        f.write(file_content)
    os.environ[LOG_ENV_VARIABLE_NAME] = str(custom_log_path)
    tasks = run_n_simple_tasks(1)
    assert tasks[0]["log_path"] == custom_log_path
    with open(custom_log_path, "r") as f:
        content = f.read()
        assert file_content in content
    os.environ.pop(LOG_ENV_VARIABLE_NAME)


def test_same_logging_file_custom_log_path(set_tempdir):
    """
    Integration test which verifies that re-using the same logging for multiple tasks works as expected,
    using a custom log path
    """
    temp_dir = set_tempdir
    custom_log_path = Path(temp_dir) / "main.log"
    os.environ[LOG_ENV_VARIABLE_NAME] = str(custom_log_path)
    tasks = run_n_simple_tasks(5)
    for task in tasks:
        assert task["log_path"] == custom_log_path
    os.environ.pop(LOG_ENV_VARIABLE_NAME)


def test_different_custom_logging_file(set_tempdir):
    """
    Integration test which verifies that changing the log path from one invocation of run_task to the next will work
    """
    temp_dir = set_tempdir
    task_creator = lambda: generate_root_task(task_class=TestTask_env, x="Test")

    use_specific_log_file(task_creator, temp_dir, "first")
    use_specific_log_file(task_creator, temp_dir, "second")


def test_custom_log_path_points_at_dir(set_tempdir):
    """
    Integration test which verifies that using a custom log path for a single task fails if the path points to a directory instead of a file
    """
    temp_dir = set_tempdir
    custom_log_path = Path(temp_dir)
    os.environ[LOG_ENV_VARIABLE_NAME] = str(custom_log_path)

    with pytest.raises(Exception) as e:
        run_n_simple_tasks(1)

    assert e.type.__name__ == "IsADirectoryError"
    os.environ.pop(LOG_ENV_VARIABLE_NAME)


def test_missing_dir_in_custom_log_path(set_tempdir):
    """
    Integration test which verifies that all not preexisting dirs in a custom log path are created correctly.
    """
    temp_dir = set_tempdir
    custom_log_path = Path(temp_dir) / "another_dir" / "main.log"
    os.environ[LOG_ENV_VARIABLE_NAME] = str(custom_log_path)
    tasks = run_n_simple_tasks(1)
    assert tasks[0]["log_path"] == custom_log_path
    os.environ.pop(LOG_ENV_VARIABLE_NAME)

