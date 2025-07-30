from exasol_integration_test_docker_environment.lib.logging.abstract_log_handler import (
    AbstractLogHandler,
)
from exasol_integration_test_docker_environment.lib.models.config.log_config import (
    WriteLogFilesToConsole,
)


class ContainerLogHandler(AbstractLogHandler):

    def __init__(self, log_file_path, logger, description: str) -> None:
        super().__init__(log_file_path, logger)
        self.db_container_name = description

    def handle_log_line(self, log_line, error: bool = False) -> None:
        self._log_file.write(log_line + "\n")
        self._complete_log.append(log_line)

    def get_complete_log(self) -> list[str]:
        return self._complete_log

    def finish(self) -> None:
        if self._log_config.write_log_files_to_console == WriteLogFilesToConsole.all:
            self._logger.info(
                "Log %s\n%s", self.db_container_name, "\n".join(self._complete_log)
            )
