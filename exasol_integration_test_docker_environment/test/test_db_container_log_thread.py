import logging
import tempfile
import time
import unittest
from pathlib import Path
from typing import List

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.test_environment.database_waiters.db_container_log_thread import \
    DBContainerLogThread


class ReturnValueRunTaskTest(unittest.TestCase):

    def setUp(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def _build_docker_command(self, logs: List[str]):
        """
        Builds a bash while loop command which can be used to print logs.
        Args:
            logs: List of logs to print, each in one line.

        Returns:
            Something like ["bash", "-c", "while true; do echo 'Test'; done"]
        """
        echo_commands = [f"echo '{log}'" for log in logs]
        echo_commdands_str = ";".join(echo_commands)
        bash_command = f"while true; do {echo_commdands_str}; sleep 0.1; done"
        return ["bash", "-c", bash_command]

    def _run_container_log_thread(self, logs: List[str]) -> str:
        with tempfile.TemporaryDirectory() as tmpDir:
            with ContextDockerClient(timeout=3600) as client:
                try:
                    container = client.containers.run("ubuntu", self._build_docker_command(logs), detach=True)
                    thread = DBContainerLogThread(container, self.logger, Path(tmpDir) / "log.txt", "test")
                    thread.start()
                    time.sleep(2)
                    thread.stop()
                finally:
                    container.stop()
                    container.remove()
                return thread.error_message

    def test_container_log_thread_no_error(self) -> None:
        """
        Integration test which verifies that the DBContainerLogThread returns no error message if no error is logged.
        """
        error_message = self._run_container_log_thread(["test", "something", "db started"])
        self.assertEqual(None, error_message)

    def test_container_log_thread_error(self) -> None:
        """
        Integration test which verifies that the DBContainerLogThread returns error message if error is logged.
        """
        error_message = self._run_container_log_thread(["confd returned with state 1"])
        self.assertIn("confd returned with state 1\n", error_message)

    def test_container_ignore_rsyslogd(self) -> None:
        """
        Integration test which verifies that the DBContainerLogThread returns no error message if rsyslogd crashes.
        """
        rsys_logd_logs = [
            "[2024-09-17 14:12:20.335085 +00:00] child 58687 (Part:9 Node:0 rsyslogd) returned with state 1.",
            "[2024-09-17 14:12:20.336886 +00:00] Started /sbin/rsyslogd with PID:58688 UID:0 GID:0 Part:9 Node:0",
            "[2024-09-17 14:12:20.336967 +00:00] 30 auto-restarted processes exited in the last 0 seconds. Starting to delay process death handling."
        ]
        error_message = self._run_container_log_thread(rsys_logd_logs)
        self.assertEqual(None, error_message)

if __name__ == '__main__':
    unittest.main()
