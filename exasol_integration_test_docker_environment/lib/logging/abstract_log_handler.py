from pathlib import Path

from exasol_integration_test_docker_environment.lib.base.task_logger_wrapper import (
    TaskLoggerWrapper,
)
from exasol_integration_test_docker_environment.lib.models.config.log_config import (
    log_config,
)


class AbstractLogHandler:

    def __init__(self, log_file_path: Path, logger: TaskLoggerWrapper) -> None:
        self._log_file_path = log_file_path
        self._logger = logger
        self._complete_log: list[str] = []
        self._error_message = None
        self._log_config = log_config()

    def __enter__(self):
        if self._log_file_path is not None:
            self._log_file = self._log_file_path.open("w")
        return self

    def __exit__(self, type, value, traceback) -> None:
        if self._log_file_path is not None:
            self._log_file.close()
        self.finish()

    def handle_log_lines(self, log_lines, error: bool = False) -> None:
        log_lines = log_lines.decode("utf-8")
        log_lines = log_lines.strip("\r\n")
        for log_line in log_lines.split("\n"):
            log_line = log_line.strip("\r\n")
            self.handle_log_line(log_line, error)

    def handle_log_line(self, log_line, error: bool = False) -> None:
        pass

    def finish(self) -> None:
        pass
