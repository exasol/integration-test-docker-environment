import sys
from datetime import datetime
from traceback import print_tb
from typing import Optional

from exasol_integration_test_docker_environment.lib.models.api_errors import (
    TaskRuntimeError,
)


def print_err(*args, **kwargs):
    kwargs["file"] = sys.stderr
    print(*args, **kwargs)


class TerminationHandler:
    """
    This helper class measures and logs time duration of the job and also logs the error message.
    """

    def __init__(self) -> None:
        self._start_time: Optional[datetime] = None

    def __enter__(self) -> None:
        self._start_time = datetime.now()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        exit_value = 0
        if exc_type == TaskRuntimeError:
            self._handle_failure(exc_val)
            exit_value = 1
        elif exc_type is None and exc_val is None and exc_tb is None:
            self._handle_success()
        else:
            self._handle_unexpected_failure(exc_val, exc_tb)
            exit_value = 1
        sys.exit(exit_value)

    def _handle_unexpected_failure(self, exc_val, exc_tb) -> None:
        assert self._start_time is not None
        timedelta = datetime.now() - self._start_time
        print_err("The command failed after %s s with:" % timedelta.total_seconds())
        print_err("Caught exception:%s" % exc_val)
        print_tb(exc_tb, file=sys.stderr)

    def _handle_failure(self, task_error: TaskRuntimeError) -> None:
        assert self._start_time is not None
        timedelta = datetime.now() - self._start_time
        print_err("The command failed after %s s with:" % timedelta.total_seconds())
        self._print_task_failures(task_error)

    @staticmethod
    def _print_task_failures(task_error: TaskRuntimeError) -> None:
        print_err()
        print_err("Task failure message: %s" % task_error.msg)
        print_err(task_error.__cause__.args[0])  # type: ignore
        print_err()

    def _handle_success(self) -> None:
        assert self._start_time is not None
        timedelta = datetime.now() - self._start_time
        print_err("The command took %s s" % timedelta.total_seconds())
