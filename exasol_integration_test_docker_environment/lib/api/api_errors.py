from typing import Optional, List


class ArgumentConstraintError(ValueError):
    """Represents an error for an argument not fulfilling a specific constraint"""


class HealthProblem(RuntimeError):
    """Represents a problem found by analyzing the project health"""


class TaskRuntimeError(RuntimeError):
    """Represents an error which occurred during execution of a luigi task"""
    def __init__(self, msg, inner: Optional[List[str]] = None):
        self.msg = msg
        self.inner = inner
