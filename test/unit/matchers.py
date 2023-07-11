from pathlib import Path


class UsedLogPath:
    def __init__(self, log_path: Path, task_input_parameter):
            self.log_path = log_path
            self.task_input_parameter = task_input_parameter

    def __repr__(self):
        return f"UsedLogPath({str(self.log_path)}, {self.task_input_parameter})"


class LogPathCorrectnessMatcher:
    """Assert that a given path meets some expectations."""

    def __init__(self, expected_log_path: Path):
        self.expected_log_path = expected_log_path

    def __eq__(self, used_log_path: UsedLogPath):
        log_path = used_log_path.log_path
        if not (log_path == self.expected_log_path
                and log_path.exists()
                and log_path.is_file()):
            return False

        with open(log_path, "r") as f:
            log_content = f.read()
            return f"Logging: {used_log_path.task_input_parameter}" in log_content

    def __repr__(self):
        return f"LogPathCorrectnessMatcher({str(self.expected_log_path)})"
