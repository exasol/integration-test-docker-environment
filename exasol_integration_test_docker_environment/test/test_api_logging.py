import contextlib
import logging
import sys
import tempfile
import unittest
import warnings
from contextlib import redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import (
    Any,
    Dict,
    Optional,
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

from exasol_integration_test_docker_environment.lib.api.common import (
    generate_root_task,
    run_task,
    set_build_config,
)
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
        self.return_object("DUMMY SUCCES")


@contextlib.contextmanager
def catch_stderr():
    with tempfile.TemporaryFile("w+t") as temp_file:
        try:
            with ignore_resource_warning():
                with redirect_stderr(temp_file) as catched_stderr:
                    yield catched_stderr
        finally:
            temp_file.seek(0)
            print(temp_file.read(), file=sys.stderr)


class APIClientLoggingTest(unittest.TestCase):

    def setUp(self):
        self.old_max_length = unittest.util._MAX_LENGTH
        unittest.util._MAX_LENGTH = 20000
        print(f"SetUp {self.__class__.__name__}", file=sys.stderr)
        self._build_output_temp_dir = TemporaryDirectory()
        self._build_output_temp_dir.__enter__()
        self.reset_logging()

    def tearDown(self):
        self._build_output_temp_dir.__exit__(None, None, None)
        self.reset_logging()
        unittest.util._MAX_LENGTH = self.old_max_length

    @ignore_resource_warning()
    def dummy_api_command(
        self, log_level: Optional[str], use_job_specific_log_file: bool
    ):
        set_build_config(
            False,
            tuple(),
            False,
            False,
            self._build_output_temp_dir.name,
            "/tmp",
            "",
            "test",
        )
        task_creator = lambda: generate_root_task(task_class=DummyTask)
        result = run_task(
            task_creator=task_creator,
            workers=2,
            task_dependencies_dot_file=None,
            log_level=log_level,
            use_job_specific_log_file=use_job_specific_log_file,
        )
        return result

    def configure_logging(self, log_level: int):
        logging.basicConfig(
            format=f"{TEST_FORMAT} %(levelname)s %(message)s",
            level=log_level,
            force=True,
        )

    def assert_loggers_are_equal(self, logger_infos_after, logger_infos_before):
        self.assertEqual(
            logger_infos_before[ROOT_LOGGER], logger_infos_after[ROOT_LOGGER]
        )
        self.assertEqual(
            logger_infos_before[API_CLIENT_LOGGING_TEST_LOGGER],
            logger_infos_after[API_CLIENT_LOGGING_TEST_LOGGER],
        )
        self.assertEqual(
            logger_infos_before[LUIGI_LOGGER], logger_infos_after[LUIGI_LOGGER]
        )
        self.assertEqual(
            logger_infos_before[LUIGI_INTERFACE_LOGGER],
            logger_infos_after[LUIGI_INTERFACE_LOGGER],
        )

    def create_test_regex(self, log_level: int):
        level_name = logging.getLevelName(log_level)
        return f".*{TEST_FORMAT} {level_name} DummyTask_.* DUMMY LOGGER {level_name}.*"

    def test_luigi_log_level_info_and_basic_logging_error(self):
        with catch_stderr() as catched_stderr:
            self.configure_logging(log_level=logging.ERROR)
            logger_infos_before = self.create_logger_infos()
            result = self.dummy_api_command(
                log_level="INFO", use_job_specific_log_file=False
            )
            logger_infos_after = self.create_logger_infos()
            self.assert_loggers_are_equal(logger_infos_after, logger_infos_before)
            catched_stderr.seek(0)
            stderr_output = catched_stderr.read()
            self.assertNotEqual(catched_stderr, "")
            self.assertRegex(stderr_output, self.create_test_regex(logging.ERROR))
            self.assertRegex(stderr_output, self.create_test_regex(logging.INFO))
            self.assertRegex(stderr_output, ".*===== Luigi Execution Summary =====.*")
            main_log_glob = list(
                Path(self._build_output_temp_dir.name).glob("**/main.log")
            )
            self.assertEqual(main_log_glob, [])

    def test_luigi_log_level_error_and_basic_logging_info(self):
        with catch_stderr() as catched_stderr:
            self.configure_logging(log_level=logging.INFO)
            logger_infos_before = self.create_logger_infos()
            result = self.dummy_api_command(
                log_level="ERROR", use_job_specific_log_file=False
            )
            logger_infos_after = self.create_logger_infos()
            self.assert_loggers_are_equal(logger_infos_after, logger_infos_before)
            catched_stderr.seek(0)
            stderr_output = catched_stderr.read()
            self.assertNotEqual(catched_stderr, "")
            self.assertRegex(stderr_output, self.create_test_regex(logging.ERROR))
            self.assertNotRegex(stderr_output, self.create_test_regex(logging.INFO))
            main_log_glob = list(
                Path(self._build_output_temp_dir.name).glob("**/main.log")
            )
            self.assertEqual(main_log_glob, [])

    def test_luigi_log_level_error_multiple_calls_and_basic_logging_info(self):
        with catch_stderr() as catched_stderr:
            self.configure_logging(log_level=logging.INFO)
            logger_infos_before = self.create_logger_infos()
            result = self.dummy_api_command(
                log_level="ERROR", use_job_specific_log_file=False
            )
            result = self.dummy_api_command(
                log_level="ERROR", use_job_specific_log_file=False
            )
            logger_infos_after = self.create_logger_infos()
            self.assert_loggers_are_equal(logger_infos_after, logger_infos_before)
            catched_stderr.seek(0)
            stderr_output = catched_stderr.read()
            self.assertNotEqual(catched_stderr, "")
            self.assertRegex(stderr_output, self.create_test_regex(logging.ERROR))
            self.assertNotRegex(stderr_output, self.create_test_regex(logging.INFO))
            self.assertEqual(2, stderr_output.count("DUMMY LOGGER ERROR"))
            main_log_glob = list(
                Path(self._build_output_temp_dir.name).glob("**/main.log")
            )
            self.assertEqual(main_log_glob, [])

    def test_luigi_use_job_specific_log_file_and_basic_logging_error(self):
        with catch_stderr() as catched_stderr:
            self.configure_logging(log_level=logging.ERROR)
            logger_infos_before = self.create_logger_infos()
            result = self.dummy_api_command(
                log_level=None, use_job_specific_log_file=True
            )
            logger_infos_after = self.create_logger_infos()
            self.assert_loggers_are_equal(logger_infos_after, logger_infos_before)
            catched_stderr.seek(0)
            stderr_output = catched_stderr.read()
            self.assert_loggers_are_equal(logger_infos_after, logger_infos_before)
            # Python3.12 (and later?) prints a deprecation warning.
            if sys.version_info[1] < 12:
                self.assertEqual(stderr_output, "")
            else:
                stderr_output_lines = stderr_output.split("\n")
                self.assertEqual(len(stderr_output_lines), 3)
                self.assertIn(
                    " is multi-threaded, use of fork() may lead to deadlocks in the child",
                    stderr_output_lines[0],
                )
                self.assertEqual(stderr_output_lines[1], "  self.pid = os.fork()")
                self.assertEqual(stderr_output_lines[2], "")
            main_log_glob = list(
                Path(self._build_output_temp_dir.name).glob("**/main.log")
            )
            self.assertNotEqual(main_log_glob, [])

    def test_luigi_no_log_config_and_basic_logging_info(self):
        with catch_stderr() as catched_stderr:
            self.configure_logging(log_level=logging.INFO)
            logger_infos_before = self.create_logger_infos()
            result = self.dummy_api_command(
                log_level=None, use_job_specific_log_file=False
            )
            logger_infos_after = self.create_logger_infos()
            self.assert_loggers_are_equal(logger_infos_after, logger_infos_before)
            catched_stderr.seek(0)
            stderr_output = catched_stderr.read()
            self.assertRegex(stderr_output, self.create_test_regex(logging.ERROR))
            self.assertRegex(stderr_output, self.create_test_regex(logging.INFO))
            self.assertRegex(stderr_output, ".*===== Luigi Execution Summary =====.*")
            main_log_glob = list(
                Path(self._build_output_temp_dir.name).glob("**/main.log")
            )
            self.assertEqual(main_log_glob, [])

    def test_luigi_no_log_config_and_basic_logging_error(self):
        with catch_stderr() as catched_stderr:
            self.configure_logging(log_level=logging.ERROR)
            logger_infos_before = self.create_logger_infos()
            result = self.dummy_api_command(
                log_level=None, use_job_specific_log_file=False
            )
            logger_infos_after = self.create_logger_infos()
            self.assert_loggers_are_equal(logger_infos_after, logger_infos_before)
            catched_stderr.seek(0)
            stderr_output = catched_stderr.read()
            self.assertNotEqual(stderr_output, "")
            self.assertRegex(stderr_output, self.create_test_regex(logging.ERROR))
            self.assertNotRegex(stderr_output, self.create_test_regex(logging.INFO))
            main_log_glob = list(
                Path(self._build_output_temp_dir.name).glob("**/main.log")
            )
            self.assertEqual(main_log_glob, [])

    def reset_logging(self):
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

    def create_logger_infos(self) -> Dict[str, Dict[str, Any]]:
        logger_infos = {
            ROOT_LOGGER: self.get_logger_info(logging.root),
            API_CLIENT_LOGGING_TEST_LOGGER: self.get_logger_info(
                logging.getLogger("APIClientLoggingTest")
            ),
            LUIGI_LOGGER: self.get_logger_info(logging.getLogger("luigi")),
            LUIGI_INTERFACE_LOGGER: self.get_logger_info(
                logging.getLogger("luigi-interface")
            ),
        }
        return logger_infos

    def get_logger_info(self, logger: logging.Logger) -> Dict[str, Any]:
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


if __name__ == "__main__":
    unittest.main()
