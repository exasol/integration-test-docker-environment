import contextlib
import logging
import re
import sys
import warnings
from typing import (
    Any,
    Dict,
    Optional,
)

import pytest

from exasol_integration_test_docker_environment.lib.base.run_task import (
    generate_root_task,
    run_task,
)
from exasol_integration_test_docker_environment.lib.models.config.build_config import (
    set_build_config,
)

LOGGER_STR = "logger_str"

LEVEL_NAME = "level_name"

PARENT = "parent"

PROPAGATE = "propagate"

DISABLED = "disabled"

FILTERS = "filters"

LOGGER_NAME = "name"

HANDLERS = "handlers"

LEVEL = "level"

OBJECT = "object"

LUIGI_INTERFACE_LOGGER = "luigi-interface"

LUIGI_LOGGER = "luigi"

API_CLIENT_LOGGING_TEST_LOGGER = "APIClientLoggingTest"

ROOT_LOGGER = "root"

TEST_FORMAT = "TEST_FORMAT"

from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import (
    DependencyLoggerBaseTask,
)


@contextlib.contextmanager
def ignore_resource_warning():
    """
    Ignore ResourceWarning to keep the captured output clean for the asserts
    """
    with warnings.catch_warnings():
        warnings.filterwarnings(action="ignore", category=ResourceWarning)
        yield


class DummyTask(DependencyLoggerBaseTask):

    def run_task(self):
        self.logger.info("DUMMY LOGGER INFO")
        self.logger.error("DUMMY LOGGER ERROR")
        self.return_object("DUMMY SUCCESS")


def configure_logging(log_level: int):
    logging.basicConfig(
        format=f"{TEST_FORMAT} %(levelname)s %(message)s",
        level=log_level,
        force=True,
    )


def reset_logging():
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=logging.ERROR,
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )
    loggerDict = logging.root.manager.loggerDict
    for key in list(loggerDict.keys()):
        loggerDict[key].disabled = True
        del loggerDict[key]


@pytest.fixture
def custom_logging():
    @contextlib.contextmanager
    def logging_context_creator(log_level: int):
        configure_logging(log_level)
        yield
        reset_logging()

    return logging_context_creator


@pytest.fixture
def luigi_output(tmp_path):
    set_build_config(
        False,
        tuple(),
        False,
        False,
        str(tmp_path),
        str(tmp_path.parent),
        "",
        "test",
    )
    return tmp_path


@ignore_resource_warning()
def dummy_api_command(log_level: Optional[str], use_job_specific_log_file: bool):
    task_creator = lambda: generate_root_task(task_class=DummyTask)
    result = run_task(
        task_creator=task_creator,
        workers=2,
        task_dependencies_dot_file=None,
        log_level=log_level,
        use_job_specific_log_file=use_job_specific_log_file,
    )
    return result


def assert_loggers_are_equal(logger_infos_after, logger_infos_before):
    assert logger_infos_before[ROOT_LOGGER] == logger_infos_after[ROOT_LOGGER]
    assert (
        logger_infos_before[API_CLIENT_LOGGING_TEST_LOGGER]
        == logger_infos_after[API_CLIENT_LOGGING_TEST_LOGGER]
    )
    assert logger_infos_before[LUIGI_LOGGER] == logger_infos_after[LUIGI_LOGGER]
    assert (
        logger_infos_before[LUIGI_INTERFACE_LOGGER]
        == logger_infos_after[LUIGI_INTERFACE_LOGGER]
    )


def create_test_regex(log_level: int):
    level_name = logging.getLevelName(log_level)
    regex = f".*{TEST_FORMAT} {level_name} DummyTask_.* DUMMY LOGGER {level_name}.*"
    return re.compile(regex)


def test_luigi_log_level_info_and_basic_logging_error(
    capfd, custom_logging, luigi_output
):
    """
    This test checks if setting luigi log level to level INFO and global log level to ERROR
    prints error/info messages to stderr.
    Note: This test does not work with `pytest -s ...`
    """

    with custom_logging(log_level=logging.ERROR) as error_log:
        logger_infos_before = create_logger_infos()
        result = dummy_api_command(log_level="INFO", use_job_specific_log_file=False)
        logger_infos_after = create_logger_infos()
        assert_loggers_are_equal(logger_infos_after, logger_infos_before)

        stdout_output, stderr_output = capfd.readouterr()
        assert stdout_output == ""
        assert stderr_output != ""
        assert create_test_regex(logging.ERROR).search(stderr_output) is not None
        assert create_test_regex(logging.INFO).search(stderr_output) is not None
        assert (
            re.compile(".*===== Luigi Execution Summary =====.*").search(stderr_output)
            is not None
        )

        main_log_glob = list(luigi_output.glob("**/main.log"))
        assert main_log_glob == []


def test_luigi_log_level_error_and_basic_logging_info(
    capfd, custom_logging, luigi_output
):
    """
    This test checks if setting luigi log level to level ERROR and global log level to INFO
    prints only error messages to stderr, but no INFO messages to stderr.
    Note: This test does not work with `pytest -s ...`
    """
    with custom_logging(log_level=logging.INFO) as error_log:
        logger_infos_before = create_logger_infos()
        result = dummy_api_command(log_level="ERROR", use_job_specific_log_file=False)
        logger_infos_after = create_logger_infos()
        assert_loggers_are_equal(logger_infos_after, logger_infos_before)
        stdout_output, stderr_output = capfd.readouterr()
        assert stdout_output == ""
        assert stderr_output != ""
        assert create_test_regex(logging.ERROR).search(stderr_output) is not None
        assert create_test_regex(logging.INFO).search(stderr_output) is None
        main_log_glob = list(luigi_output.glob("**/main.log"))
        assert main_log_glob == []


def test_luigi_log_level_error_multiple_calls_and_basic_logging_info(
    capfd, custom_logging, luigi_output
):
    """
    This test checks if setting luigi log level to level ERROR and global log level to INFO
    prints only error messages to stderr, but no INFO messages; even when running a task multiple times.
    Note: This test does not work with `pytest -s ...`
    """
    with custom_logging(log_level=logging.INFO) as error_log:

        logger_infos_before = create_logger_infos()
        result = dummy_api_command(log_level="ERROR", use_job_specific_log_file=False)
        result = dummy_api_command(log_level="ERROR", use_job_specific_log_file=False)
        logger_infos_after = create_logger_infos()
        assert_loggers_are_equal(logger_infos_after, logger_infos_before)
        stdout_output, stderr_output = capfd.readouterr()
        assert stdout_output == ""
        assert stderr_output != ""
        assert create_test_regex(logging.ERROR).search(stderr_output) is not None
        assert create_test_regex(logging.INFO).search(stderr_output) is None
        assert 2 == stderr_output.count("DUMMY LOGGER ERROR")
        main_log_glob = list(luigi_output.glob("**/main.log"))
        assert main_log_glob == []


def test_luigi_use_job_specific_log_file_and_basic_logging_error(
    capfd, custom_logging, luigi_output
):
    """
    This test checks if setting luigi log level to None and global log level to ERROR, and using flag
    `use_job_specific_log_file`
    prints no error messages to stderr/stdout, but writes the log messages to `main.log`.
    Note: This test does not work with `pytest -s ...`
    """

    with custom_logging(log_level=logging.ERROR) as error_log:

        logger_infos_before = create_logger_infos()
        result = dummy_api_command(log_level=None, use_job_specific_log_file=True)
        logger_infos_after = create_logger_infos()
        assert_loggers_are_equal(logger_infos_after, logger_infos_before)
        stdout_output, stderr_output = capfd.readouterr()

        # Python3.12 (and later?) prints a deprecation warning.
        if sys.version_info[1] < 12:
            assert stderr_output == ""
        else:
            stderr_output_lines = stderr_output.split("\n")
            assert len(stderr_output_lines) == 3
            assert (
                " is multi-threaded, use of fork() may lead to deadlocks in the child"
                in stderr_output_lines[0]
            )
            assert stderr_output_lines[1] == "  self.pid = os.fork()"
            assert stderr_output_lines[2] == ""
        main_log_glob = list(luigi_output.glob("**/main.log"))
        assert len(main_log_glob) > 0


def test_luigi_no_log_config_and_basic_logging_info(
    capfd, custom_logging, luigi_output
):
    """
    This test checks if setting luigi log level to None and global log level to INFO
    prints error/info messages to stderr.
    Note: This test does not work with `pytest -s ...`
    """
    with custom_logging(log_level=logging.INFO) as error_log:
        logger_infos_before = create_logger_infos()
        result = dummy_api_command(log_level=None, use_job_specific_log_file=False)
        logger_infos_after = create_logger_infos()
        assert_loggers_are_equal(logger_infos_after, logger_infos_before)
        stdout_output, stderr_output = capfd.readouterr()
        assert stdout_output == ""
        assert stderr_output != ""

        assert create_test_regex(logging.ERROR).search(stderr_output) is not None
        assert create_test_regex(logging.INFO).search(stderr_output) is not None
        assert (
            re.compile(".*===== Luigi Execution Summary =====.*").search(stderr_output)
            is not None
        )
        main_log_glob = list(luigi_output.glob("**/main.log"))
        assert main_log_glob == []


def test_luigi_no_log_config_and_basic_logging_error(
    capfd, custom_logging, luigi_output
):
    """
    This test checks if setting luigi log level to None and global log level to ERROR
    prints error messages to stderr, but no INFO messages.
    Note: This test does not work with `pytest -s ...`
    """
    with custom_logging(log_level=logging.ERROR) as error_log:
        logger_infos_before = create_logger_infos()
        result = dummy_api_command(log_level=None, use_job_specific_log_file=False)
        logger_infos_after = create_logger_infos()
        assert_loggers_are_equal(logger_infos_after, logger_infos_before)
        stdout_output, stderr_output = capfd.readouterr()
        assert stdout_output == ""
        assert stderr_output != ""

        assert create_test_regex(logging.ERROR).search(stderr_output) is not None
        assert create_test_regex(logging.INFO).search(stderr_output) is None
        main_log_glob = list(luigi_output.glob("**/main.log"))
        assert main_log_glob == []


def create_logger_infos() -> Dict[str, Dict[str, Any]]:
    logger_infos = {
        ROOT_LOGGER: get_logger_info(logging.root),
        API_CLIENT_LOGGING_TEST_LOGGER: get_logger_info(
            logging.getLogger("APIClientLoggingTest")
        ),
        LUIGI_LOGGER: get_logger_info(logging.getLogger("luigi")),
        LUIGI_INTERFACE_LOGGER: get_logger_info(logging.getLogger("luigi-interface")),
    }
    return logger_infos


def get_logger_info(logger: logging.Logger) -> Dict[str, Any]:
    logger_info: Dict[str, Any] = dict()
    logger_info[LOGGER_STR] = str(logger)
    logger_info[LEVEL] = logger.level
    logger_info[LEVEL_NAME] = logging.getLevelName(logger.level)
    logger_info[HANDLERS] = list(logger.handlers)
    logger_info[LOGGER_NAME] = logger.name
    logger_info[FILTERS] = list(logger.filters)
    logger_info[DISABLED] = logger.disabled
    logger_info[PROPAGATE] = logger.propagate
    logger_info[PARENT] = logger.parent
    return logger_info
