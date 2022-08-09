
class ArgumentConstraintError(ValueError):
    """Represents an error for an argument not fulfilling a specific constraint"""
    pass


class HealthProblem(RuntimeError):
    """Represents a problem found by analyzing the project health"""
    pass


class TaskRuntimeError(RuntimeError):
    """Represents an error which occurred during execution of a luigi task"""
    pass
