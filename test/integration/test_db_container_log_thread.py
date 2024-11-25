import logging
import tempfile
import time
from pathlib import Path
from typing import List, Optional

import pytest

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.test_environment.database_waiters.db_container_log_thread import (
    DBContainerLogThread,
)


def _build_docker_command(logs: List[str]):
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


def _run_container_log_thread(logger, logs: List[str]) -> Optional[str]:
    """
    Starts a dummy docker container which prints logs in an endless loop, and calls DBContainerLogThread on that container.

    Returns: resulting DBContainerLogThread.error_message
    """
    with tempfile.TemporaryDirectory() as tmpDir:
        with ContextDockerClient(timeout=3600) as client:
            try:
                container = client.containers.run(
                    "ubuntu", _build_docker_command(logs), detach=True
                )
                thread = DBContainerLogThread(
                    container, logger, Path(tmpDir) / "log.txt", "test"
                )
                thread.start()
                time.sleep(2)
                thread.stop()
            finally:
                container.stop()
                container.remove()
            return thread.error_message


@pytest.fixture
def test_logger():
    return logging.Logger(__name__)


def test_container_log_thread_no_error(test_logger) -> None:
    """
    Integration test which verifies that the DBContainerLogThread returns no error message if no error is logged.
    """
    error_message = _run_container_log_thread(
        test_logger, ["test", "something", "db started"]
    )
    assert error_message is None


def test_container_log_thread_error(test_logger) -> None:
    """
    Integration test which verifies that the DBContainerLogThread returns error message if error is logged.
    """
    error_message = _run_container_log_thread(
        test_logger, ["confd returned with state 1"]
    )
    assert error_message and "confd returned with state 1\n" in error_message


def test_container_log_thread_ignore_rsyslogd(test_logger) -> None:
    """
    Integration test which verifies that the DBContainerLogThread returns no error message if rsyslogd crashes.
    """
    rsys_logd_logs = [
        "[2024-09-17 14:12:20.335085 +00:00] child 58687 (Part:9 Node:0 rsyslogd) returned with state 1.",
        "[2024-09-17 14:12:20.336886 +00:00] Started /sbin/rsyslogd with PID:58688 UID:0 GID:0 Part:9 Node:0",
        "[2024-09-17 14:12:20.336967 +00:00] 30 auto-restarted processes exited in the last 0 seconds. Starting to delay process death handling.",
    ]
    error_message = _run_container_log_thread(test_logger, rsys_logd_logs)
    assert error_message is None


def test_container_log_thread_ignore_sshd(test_logger) -> None:
    """
    Integration test which verifies that the DBContainerLogThread returns no error message if sshd crashes.
    """
    sshd_logs = [
        "[2024-09-17 14:12:20.335085 +00:00] error : sshd was not started.",
    ]
    error_message = _run_container_log_thread(test_logger, sshd_logs)
    assert error_message is None


def test_container_log_thread_exception(test_logger) -> None:
    """
    Integration test which verifies that the DBContainerLogThread returns an error message if an exception was thrown.
    """
    sshd_logs = [
        "Traceback (most recent call last):",
        'File "/opt/cos/something.py", line 364, in runcode',
        "    coro = func()",
        '  File "<input>", line 1, in <module>',
        "Exception: bad thing happend",
    ]
    error_message = _run_container_log_thread(test_logger, sshd_logs)
    assert error_message and "exception: bad thing happend\n" in error_message
