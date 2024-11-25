from exasol_integration_test_docker_environment.lib.config.log_config import log_config


class AbstractLogHandler:

    def __init__(self, log_file_path, logger):
        self._log_file_path = log_file_path
        self._logger = logger
        self._complete_log = []
        self._error_message = None
        self._log_config = log_config()

    def __enter__(self):
        if self._log_file_path is not None:
            self._log_file = self._log_file_path.open("w")
        return self

    def __exit__(self, type, value, traceback):
        if self._log_file_path is not None:
            self._log_file.close()
        self.finish()

    def handle_log_lines(self, log_lines, error: bool = False):
        log_lines = log_lines.decode("utf-8")
        log_lines = log_lines.strip("\r\n")
        result = []
        for log_line in log_lines.split("\n"):
            log_line = log_line.strip("\r\n")
            result.append(self.handle_log_line(log_line, error))
        return result

    def handle_log_line(self, log_line, error: bool = False):
        pass

    def finish(self):
        pass
