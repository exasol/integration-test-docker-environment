from test.integration.base_task.base_task import TestBaseTask

import luigi
from luigi import Parameter

from exasol_integration_test_docker_environment.lib.base.run_task import (
    generate_root_task,
)


class RootTestTask(TestBaseTask):

    def register_required(self):
        tasks = [
            self.create_child_task(task_class=ChildTestTask, p=f"{i}")
            for i in range(10)
        ]
        self.register_dependencies(tasks)

    def run_task(self):
        pass


class ChildTestTask(TestBaseTask):
    p = Parameter()

    def register_required(self):
        self.register_dependency(self.create_child_task(task_class=GrandChildTestTask))

    def run_task(self):
        pass


class GrandChildTestTask(TestBaseTask):
    def run_task(self):
        raise Exception("%s" % self.task_id)


def test_collect_failures_one_task_fails_but_is_dependency_of_multiple(luigi_output):
    task = generate_root_task(task_class=RootTestTask)
    result = luigi.build([task], workers=3, local_scheduler=True, log_level="INFO")
    assert not result
    failures = task.collect_failures()
    assert len(failures) == 1
