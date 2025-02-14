import os.path
from pathlib import Path
from unittest import mock

import luigi
import pytest

from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import (
    DependencyLoggerBaseTask,
)
from exasol_integration_test_docker_environment.lib.base.run_task import (
    generate_root_task,
    run_task,
)
from exasol_integration_test_docker_environment.lib.logging.luigi_log_config import (
    LOG_ENV_VARIABLE_NAME,
    get_log_path,
)
from exasol_integration_test_docker_environment.lib.models.config.build_config import (
    build_config,
)


@pytest.fixture
def set_tempdir(tmp_path):
    path_old = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(path_old)


@pytest.fixture()
def mock_settings_env_vars():
    with mock.patch.dict(os.environ, {}):
        yield


class UsedLogPath:
    def __init__(self, task) -> None:
        self.log_path = Path(task["log_path"])
        self.task_input_parameter = task["in_parameter"]

    def __repr__(self):
        return (
            f"log path: {str(self.log_path)}"
            f"\nlog content: '{self.log_path.read_text()}'"
        )


class LogPathCorrectnessMatcher:
    """Assert that a given path meets some expectations."""

    def __init__(self, expected_log_path: Path) -> None:
        self.expected_log_path = expected_log_path

    def __eq__(self, used_log_path: object):
        if not isinstance(used_log_path, UsedLogPath):
            return False
        log_path = used_log_path.log_path
        if not (
            log_path == self.expected_log_path
            and log_path.exists()
            and log_path.is_file()
        ):
            return False

        log_content = log_path.read_text()
        return f"Logging: {used_log_path.task_input_parameter}" in log_content

    def __repr__(self):
        return (
            f"log path: {str(self.expected_log_path)}"
            f"\nlog content: '.*Logging: {self.task_input_parameter}.*'"
        )


def default_log_path(job_id):
    return Path(build_config().output_directory) / "jobs" / job_id / "logs" / "main.log"


class TestTask(DependencyLoggerBaseTask):
    x = luigi.Parameter()

    def run_task(self):
        self.logger.info(f"Logging: {self.x}")
        self.return_object({"job_id": self.job_id, "parameter": self.x})


def run_n_simple_tasks(task_number):
    NUMBER_TASK = task_number
    task_id_generator = (x for x in range(NUMBER_TASK))
    tasks = []

    def create_task():
        return generate_root_task(task_class=TestTask, x=f"{next(task_id_generator)}")

    for j in range(NUMBER_TASK):
        output = run_task(
            create_task,
            workers=5,
            task_dependencies_dot_file=None,
            use_job_specific_log_file=True,
        )
        jobid = output["job_id"]
        log_path = get_log_path(jobid)
        tasks.append(
            {"jobid": jobid, "log_path": log_path, "in_parameter": output["parameter"]}
        )

    return tasks


def use_specific_log_file(task_creator, temp_dir, test_name):
    log_path = Path(temp_dir) / (test_name + ".log")
    os.environ[LOG_ENV_VARIABLE_NAME] = str(log_path)
    run_task(
        task_creator,
        workers=5,
        task_dependencies_dot_file=None,
        use_job_specific_log_file=True,
    )
    return log_path


def test_var_not_set(set_tempdir):
    """
    Integration test which verifies that not setting the env var LOG_ENV_VARIABLE_NAME works and uses the
    default log path
    """
    tasks = run_n_simple_tasks(1)

    log_path_matcher = LogPathCorrectnessMatcher(default_log_path(tasks[0]["jobid"]))
    log_path = UsedLogPath(tasks[0])
    assert log_path == log_path_matcher


def test_var_not_set_same_logging_file(set_tempdir):
    """
    Integration test which verifies that re-using the same logging for multiple tasks works as expected,
    using the default log path
    """
    tasks = run_n_simple_tasks(5)
    for task in tasks:
        log_path_matcher = LogPathCorrectnessMatcher(default_log_path(task["jobid"]))
        log_path = UsedLogPath(task)
        assert log_path == log_path_matcher


def test_custom_log_path_points_at_file(set_tempdir, mock_settings_env_vars):
    """
    Integration test which verifies that using a custom log path for a single task works if the path points to a file
    """
    temp_dir = set_tempdir
    custom_log_path = Path(temp_dir) / "main.log"
    log_path_matcher = LogPathCorrectnessMatcher(custom_log_path)
    os.environ[LOG_ENV_VARIABLE_NAME] = str(custom_log_path)

    tasks = run_n_simple_tasks(1)

    log_path = UsedLogPath(tasks[0])
    assert log_path == log_path_matcher


def test_preexisting_custom_log_file(set_tempdir, mock_settings_env_vars):
    """
    Integration test which verifies that using a custom log path for a single task works if file already exists.
    """
    temp_dir = set_tempdir
    custom_log_path = Path(temp_dir) / "main.log"
    log_path_matcher = LogPathCorrectnessMatcher(custom_log_path)
    os.environ[LOG_ENV_VARIABLE_NAME] = str(custom_log_path)
    file_content = "This existing file has content."
    with open(custom_log_path, "a") as f:
        f.write(file_content)

    tasks = run_n_simple_tasks(1)

    log_path = UsedLogPath(tasks[0])
    assert log_path == log_path_matcher

    with open(custom_log_path) as f:
        log_content = f.read()
        assert file_content in log_content


def test_same_logging_file_custom_log_path(set_tempdir, mock_settings_env_vars):
    """
    Integration test which verifies that re-using the same log file for multiple tasks works as expected,
    using a custom log path
    """
    temp_dir = set_tempdir
    custom_log_path = Path(temp_dir) / "main.log"
    log_path_matcher = LogPathCorrectnessMatcher(custom_log_path)
    os.environ[LOG_ENV_VARIABLE_NAME] = str(custom_log_path)
    tasks = run_n_simple_tasks(5)

    for task in tasks:
        log_path = UsedLogPath(task)
        assert log_path == log_path_matcher


def test_different_custom_logging_file(set_tempdir, mock_settings_env_vars):
    """
    Integration test which verifies that changing the log path from one invocation of run_task to the next will work
    """
    temp_dir = set_tempdir
    task_creator = lambda: generate_root_task(task_class=TestTask, x="Test")

    log_path_1 = use_specific_log_file(task_creator, temp_dir, "first")
    log_path_2 = use_specific_log_file(task_creator, temp_dir, "second")

    for log_path in [log_path_1, log_path_2]:
        assert log_path.exists()
        with open(log_path) as f:
            log_content = f.read()
            assert f"Logging: Test" in log_content


def test_custom_log_path_points_at_dir(set_tempdir, mock_settings_env_vars):
    """
    Integration test which verifies that using a custom log path for a single task fails if the path points to a directory instead of a file
    """
    temp_dir = set_tempdir
    custom_log_path = Path(temp_dir)
    os.environ[LOG_ENV_VARIABLE_NAME] = str(custom_log_path)

    with pytest.raises(IsADirectoryError):
        run_n_simple_tasks(1)


def test_missing_dir_in_custom_log_path(set_tempdir, mock_settings_env_vars):
    """
    Integration test which verifies that all not preexisting dirs in a custom log path are created correctly.
    """
    temp_dir = set_tempdir
    custom_log_path = Path(temp_dir) / "another_dir" / "main.log"
    log_path_matcher = LogPathCorrectnessMatcher(custom_log_path)
    os.environ[LOG_ENV_VARIABLE_NAME] = str(custom_log_path)
    tasks = run_n_simple_tasks(1)

    log_path = UsedLogPath(tasks[0])
    assert log_path == log_path_matcher
