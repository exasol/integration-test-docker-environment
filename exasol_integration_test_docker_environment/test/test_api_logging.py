import glob
import logging
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from sys import stderr
from tempfile import TemporaryDirectory
from typing import Any, Dict, Optional

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

from exasol_integration_test_docker_environment.lib.api.common import generate_root_task, run_task, \
    set_build_config
from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import \
    DependencyLoggerBaseTask


class DummyTask(DependencyLoggerBaseTask):

    def run_task(self):
        self.logger.info("DUMMY LOGGER")
        self.return_object("DUMMY SUCCES")


class APIClientLoggingTest(unittest.TestCase):

    def setUp(self):
        print(f"SetUp {self.__class__.__name__}", file=stderr)
        self._build_output_temp_dir = TemporaryDirectory()
        self._build_output_temp_dir.__enter__()
        self.reset_logging()

    def tearDown(self):
        self._build_output_temp_dir.__exit__(None, None, None)

    def dummy_api_command(self, log_level: Optional[str], use_job_specific_log_file: bool):
        set_build_config(False,
                         tuple(),
                         False,
                         False,
                         self._build_output_temp_dir.name,
                         "/tmp",
                         "",
                         "test")
        task_creator = lambda: generate_root_task(task_class=DummyTask)
        result = run_task(task_creator=task_creator,
                          workers=5,
                          task_dependencies_dot_file=None,
                          log_level=log_level,
                          use_job_specific_log_file=use_job_specific_log_file)
        return result

    def test_lugi_log_level_info_and_basic_logging_error(self):
        with redirect_stderr(StringIO()) as f:
            logging.basicConfig(
                format='%(asctime)s %(levelname)-8s %(message)s',
                level=logging.ERROR,
                datefmt='%Y-%m-%d %H:%M:%S',
                force=True)
            logger_infos_before = self.create_logger_infos()
            result = self.dummy_api_command(log_level="INFO", use_job_specific_log_file=False)
            logger_infos_after = self.create_logger_infos()
        self.maxDiff = 10000
        self.assertEqual(logger_infos_before[ROOT_LOGGER], logger_infos_after[ROOT_LOGGER])
        self.assertEqual(logger_infos_before[API_CLIENT_LOGGING_TEST_LOGGER],
                         logger_infos_after[API_CLIENT_LOGGING_TEST_LOGGER])
        self.assertEqual(logger_infos_before[LUIGI_LOGGER], logger_infos_after[LUIGI_LOGGER])
        self.assertNotEqual(logger_infos_before[LUIGI_INTERFACE_LOGGER], logger_infos_after[LUIGI_INTERFACE_LOGGER])
        self.assertEqual(logger_infos_after[LUIGI_INTERFACE_LOGGER][LEVEL_NAME], "INFO")
        stderr = f.getvalue()
        self.assertNotEqual(stderr, "")
        self.assertRegex(stderr, ".*===== Luigi Execution Summary =====.*")
        main_log_glob = list(Path(self._build_output_temp_dir.name).glob("**/main.log"))
        self.assertEqual(main_log_glob, [])

    def test_lugi_use_job_specific_log_file_and_basic_logging_error(self):
        with redirect_stderr(StringIO()) as f:
            logging.basicConfig(
                format='%(asctime)s %(levelname)-8s %(message)s',
                level=logging.ERROR,
                datefmt='%Y-%m-%d %H:%M:%S',
                force=True)
            logger_infos_before = self.create_logger_infos()
            result = self.dummy_api_command(log_level=None, use_job_specific_log_file=True)
            logger_infos_after = self.create_logger_infos()
        self.maxDiff = 10000
        self.assertEqual(logger_infos_before[ROOT_LOGGER], logger_infos_after[ROOT_LOGGER])
        self.assertEqual(logger_infos_before[API_CLIENT_LOGGING_TEST_LOGGER],
                         logger_infos_after[API_CLIENT_LOGGING_TEST_LOGGER])
        self.assertNotEqual(logger_infos_before[LUIGI_LOGGER], logger_infos_after[LUIGI_LOGGER])
        self.assertNotEqual(logger_infos_before[LUIGI_INTERFACE_LOGGER], logger_infos_after[LUIGI_INTERFACE_LOGGER])
        stderr = f.getvalue()
        self.assertEqual(stderr, "")
        main_log_glob = list(Path(self._build_output_temp_dir.name).glob("**/main.log"))
        self.assertNotEqual(main_log_glob, [])

    def test_lugi_log_level_error_and_basic_logging_info(self):
        with redirect_stderr(StringIO()) as f:
            logging.basicConfig(
                format='%(asctime)s %(levelname)-8s %(message)s',
                level=logging.INFO,
                datefmt='%Y-%m-%d %H:%M:%S',
                force=True)
            logger_infos_before = self.create_logger_infos()
            result = self.dummy_api_command(log_level="ERROR", use_job_specific_log_file=False)
            logger_infos_after = self.create_logger_infos()
        self.maxDiff = 10000
        self.assertEqual(logger_infos_before[ROOT_LOGGER], logger_infos_after[ROOT_LOGGER])
        self.assertEqual(logger_infos_before[API_CLIENT_LOGGING_TEST_LOGGER],
                         logger_infos_after[API_CLIENT_LOGGING_TEST_LOGGER])
        self.assertEqual(logger_infos_before[LUIGI_LOGGER], logger_infos_after[LUIGI_LOGGER])
        self.assertNotEqual(logger_infos_before[LUIGI_INTERFACE_LOGGER], logger_infos_after[LUIGI_INTERFACE_LOGGER])
        self.assertEqual(logger_infos_after[LUIGI_INTERFACE_LOGGER][LEVEL_NAME], "ERROR")
        stderr = f.getvalue()
        self.assertNotEqual(stderr, "")
        self.assertRegex(stderr, ".*logging configured by default settings")
        main_log_glob = list(Path(self._build_output_temp_dir.name).glob("**/main.log"))
        self.assertEqual(main_log_glob, [])

    def test_lugi_no_log_config_and_basic_logging_info(self):
        with redirect_stderr(StringIO()) as f:
            logging.basicConfig(
                format='%(asctime)s %(levelname)-8s %(message)s',
                level=logging.INFO,
                datefmt='%Y-%m-%d %H:%M:%S',
                force=True)
            logger_infos_before = self.create_logger_infos()
            result = self.dummy_api_command(log_level=None, use_job_specific_log_file=False)
            logger_infos_after = self.create_logger_infos()
        self.maxDiff = 30000
        self.assertEqual(logger_infos_before, logger_infos_after)
        stderr = f.getvalue()
        self.assertRegex(stderr, ".*INFO     logging disabled in settings.*")
        self.assertRegex(stderr, ".*===== Luigi Execution Summary =====.*")
        main_log_glob = list(Path(self._build_output_temp_dir.name).glob("**/main.log"))
        self.assertEqual(main_log_glob, [])

    def test_lugi_no_log_config_and_basic_logging_error(self):
        with redirect_stderr(StringIO()) as f:
            logging.basicConfig(
                format='%(asctime)s %(levelname)-8s %(message)s',
                level=logging.ERROR,
                datefmt='%Y-%m-%d %H:%M:%S',
                force=True)
            logger_infos_before = self.create_logger_infos()
            result = self.dummy_api_command(log_level=None, use_job_specific_log_file=False)
            logger_infos_after = self.create_logger_infos()
        self.maxDiff = 10000
        self.assertEqual(logger_infos_before, logger_infos_after)
        stderr = f.getvalue()
        self.assertEqual(stderr, "")
        main_log_glob = list(Path(self._build_output_temp_dir.name).glob("**/main.log"))
        self.assertEqual(main_log_glob, [])

    def reset_logging(self):
        logging.basicConfig(
            format='%(asctime)s %(levelname)-8s %(message)s',
            level=logging.ERROR,
            datefmt='%Y-%m-%d %H:%M:%S',
            force=True)
        loggerDict = logging.root.manager.loggerDict
        for key in list(loggerDict.keys()):
            loggerDict[key].disabled = True
            del loggerDict[key]

    def create_logger_infos(self) -> Dict[str, Dict[str, Any]]:
        logger_infos = {
            ROOT_LOGGER: self.get_logger_info(logging.root),
            API_CLIENT_LOGGING_TEST_LOGGER: self.get_logger_info(logging.getLogger("APIClientLoggingTest")),
            LUIGI_LOGGER: self.get_logger_info(logging.getLogger("luigi")),
            LUIGI_INTERFACE_LOGGER: self.get_logger_info(logging.getLogger("luigi-interface"))
        }
        return logger_infos

    def get_logger_info(self, logger: logging.Logger) -> Dict[str, Any]:
        logger_info = {}
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


if __name__ == '__main__':
    unittest.main()
    # test = APIClientLoggingTest()
    # try:
    #     test.setUp()
    #     test.test_lugi_log_level_info_and_basic_logging_error()
    # finally:
    #     test.tearDown()
    # try:
    #     test.setUp()
    #     test.test_lugi_log_level_error_and_basic_logging_info()
    # finally:
    #     test.tearDown()
    # try:
    #     test.setUp()
    #     test.test_lugi_no_log_config_and_basic_logging_info()
    # finally:
    #     test.tearDown()
    # try:
    #     test.setUp()
    #     test.test_lugi_no_log_config_and_basic_logging_error()
    # finally:
    #     test.tearDown()
    # try:
    #     test.setUp()
    #     test.test_lugi_use_job_specific_log_file_and_basic_logging_error()
    # finally:
    #     test.tearDown()
