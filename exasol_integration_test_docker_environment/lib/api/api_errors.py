from typing import (
    Iterable,
    List,
    Optional,
)


class ArgumentConstraintError(ValueError):
    """Represents an error for an argument not fulfilling a specific constraint"""


class HealthProblem(RuntimeError):
    """Represents a problem found by analyzing the project health"""


class TaskFailures(Exception):
    """Represents a potential cause of a TaskRuntimeError"""

    def __init__(self, inner: Optional[List[str]] = None):
        super().__init__(self._construct_exception_message(inner))
        self.inner = inner

    def _construct_exception_message(self, failures: Optional[Iterable[str]]) -> str:
        if failures is not None:
            formatted_task_failures = "\n".join(failures)
            return f"Following task failures were caught during the execution:\n{formatted_task_failures}"
        else:
            return f"No task failures were caught during the execution:"


class TaskRuntimeError(RuntimeError):
    """Represents an error which occurred during execution of a luigi task"""

    def __init__(self, msg: str, inner: Optional[List[str]] = None):
        """
        Creates a TaskRuntimeError
        Args:
            msg: The error message
            inner: A list of task failures that caused this exception
                   (@deprecated will be replaced by cause TaskFailures)
        """
        super().__init__(msg)
        self.msg = msg
        self.inner = inner
