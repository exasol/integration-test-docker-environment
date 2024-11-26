import traceback
from collections import OrderedDict
from pathlib import Path
from typing import (
    Dict,
    List,
)

from exasol_integration_test_docker_environment.lib.base.timeable_base_task import (
    TimeableBaseTask,
)


class StoppingFurtherExecution(Exception):
    pass


class StoppableBaseTask(TimeableBaseTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.failed_target = Path(super()._get_output_path_for_job(), "TASK_FAILED")

    def get_failure_log_path(self) -> Path:
        path = Path(self.get_output_path(), "failure")
        return path

    def run(self):
        try:
            self.fail_if_any_task_failed()
            task_generator = super().run()
            if task_generator is not None:
                yield from task_generator
        except Exception as exception:
            exception_tb = traceback.format_exc()
            self.handle_failure(exception, exception_tb)
            raise exception

    def fail_if_any_task_failed(self):
        if self.failed_target.exists():
            with self.failed_target.open("r") as f:
                failed_task = f.read()
            self.logger.error(
                "Task %s failed. Stopping further execution." % failed_task
            )
            raise StoppingFurtherExecution(
                "Task %s failed. Stopping further execution." % failed_task
            )

    def handle_failure(self, exception, exception_tb):
        if not isinstance(exception, StoppingFurtherExecution):
            with self.get_failure_log_path().open("w") as f:
                f.write("%s" % exception_tb)
            if not self.failed_target.exists():
                with self.failed_target.open("w") as f:
                    f.write("%s" % self.task_id)

    def collect_failures(self) -> Dict[str, None]:
        failures: Dict[str, None] = OrderedDict()
        failures.update(self.collect_failures_of_child_tasks())
        if self.get_failure_log_path().exists():
            with self.get_failure_log_path().open("r") as f:
                exception = f.read().strip()
                prefix = "    "
                formatted_exception = prefix + prefix.join(exception.splitlines(True))
                failure_message = f"- {self.task_id}:\n{formatted_exception}"
                failures[failure_message] = None

        return failures

    def collect_failures_of_child_tasks(self) -> Dict[str, None]:
        failures_of_child_tasks: Dict[str, None] = OrderedDict()
        if self._run_dependencies_target.exists():
            _run_dependencies_tasks_from_target = self._run_dependencies_target.read()
        else:
            _run_dependencies_tasks_from_target = []
        _run_dependencies_tasks = (
            self._run_dependencies_tasks + _run_dependencies_tasks_from_target
        )
        reversed_run_dependencies_task_list = list(_run_dependencies_tasks)
        reversed_run_dependencies_task_list.reverse()
        for task in reversed_run_dependencies_task_list:
            if isinstance(task, StoppableBaseTask):
                failures_of_child_tasks.update(task.collect_failures())

        reversed_registered_task_list = list(self._registered_tasks)
        reversed_registered_task_list.reverse()
        for task in reversed_registered_task_list:
            if isinstance(task, StoppableBaseTask):
                failures_of_child_tasks.update(task.collect_failures())
        return failures_of_child_tasks
