import json

from exasol_integration_test_docker_environment.lib.docker.images.image_info import (
    ImageInfo,
)
from exasol_integration_test_docker_environment.lib.logging.abstract_log_handler import (
    AbstractLogHandler,
)
from exasol_integration_test_docker_environment.lib.models.config.log_config import (
    WriteLogFilesToConsole,
)


class PushLogHandler(AbstractLogHandler):

    def __init__(self, log_file_path, logger, image_info: ImageInfo) -> None:
        super().__init__(log_file_path, logger)
        self._image_info = image_info

    def handle_log_line(self, log_line, error: bool = False) -> None:
        json_output = json.loads(log_line)
        if "status" in json_output and json_output["status"] != "Pushing":
            self._complete_log.append(json_output["status"])
            self._log_file.write(json_output["status"])
            self._log_file.write("\n")
        if "errorDetail" in json_output:
            self._error_message = json_output["errorDetail"]["message"]

    def finish(self) -> None:
        self.write_log_to_console_if_requested()
        if self._error_message is not None:
            self.write_error_log_to_console_if_requested()
            raise Exception(
                'Error occurred during the push of the image %s. Received error "%s" .'
                "The whole log can be found in %s"
                % (
                    self._image_info.get_target_complete_name(),
                    self._error_message,
                    self._log_file_path,
                )
            )

    def write_error_log_to_console_if_requested(self) -> None:
        if (
            self._log_config.write_log_files_to_console
            == WriteLogFilesToConsole.only_error
        ):
            self._logger.error(
                "Push of image %s failed\nPush Log:\n%s",
                self._image_info.get_target_complete_name(),
                "\n".join(self._complete_log),
            )

    def write_log_to_console_if_requested(self) -> None:
        if self._log_config.write_log_files_to_console == WriteLogFilesToConsole.all:
            self._logger.info(
                "Push Log of image %s\n%s",
                self._image_info.get_target_complete_name(),
                "\n".join(self._complete_log),
            )
