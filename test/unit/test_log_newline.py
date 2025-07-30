from pathlib import Path
from test.matchers import regex_matcher

from exasol_integration_test_docker_environment.lib.logging.command_log_handler import (
    CommandLogHandler,
)


def test_new_line(tmp_path):
    log_file_path = Path(tmp_path, "test_cmd_log_handler.log")
    with CommandLogHandler(log_file_path, None, "test for multi lines") as log_handler:
        log_handler.handle_log_line("log line 1")
        log_handler.handle_log_line("log line 2")
        with open(log_file_path) as log_file:
            line_count = sum(1 for line in log_file)
            assert line_count > 1


def test_timestamp(tmp_path):
    log_file_path = Path(tmp_path, "test_cmd_log_handler.log")
    with CommandLogHandler(log_file_path, None, "test for multi lines") as log_handler:
        log_handler.handle_log_line("log line 1")
    with open(log_file_path) as log_file:
        first_line = log_file.readline()
        # pattern is, 0 padded hh.mm.ss.6-digits-usecs
        assert first_line == regex_matcher(r"^\d{2}.\d{2}.\d{2}\.\d{6}")
