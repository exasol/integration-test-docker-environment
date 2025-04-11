from test.integration.base_task.base_task import TestBaseTask

import luigi
from luigi import Parameter

from exasol_integration_test_docker_environment.lib.base.run_task import (
    generate_root_task,
)


class RootTestTask(TestBaseTask):

    def run_task(self):
        tasks = [
            self.create_child_task(task_class=ChildTestTask, p=f"{i}")
            for i in range(10)
        ]
        self.logger.info(tasks)
        yield from self.run_dependencies(tasks)


class ChildTestTask(TestBaseTask):
    p = Parameter()

    def run_task(self):
        self.logger.info("Start and wait")
        import time

        time.sleep(5)
        self.logger.info("Finished wait and fail")
        raise Exception("%s" % self.task_id)


def test_collect_failures_diffrent_task_fail(luigi_output):
    """
    Test the collection of failures when multiple child tasks fail.

    This test verifies that when multiple child tasks fail in a parallel execution,
    the root task correctly collects and reports all failures. It uses a custom
    `RootTestTask` that spawns multiple `ChildTestTask` instances, each of which
    intentionally fails after a delay. The test asserts that:
    1. The Luigi build process reports a failure.
    2. The root task collects multiple failures as expected.
    """
    task = generate_root_task(task_class=RootTestTask)
    result = luigi.build([task], workers=5, local_scheduler=True, log_level="INFO")
    assert not result
    failures = task.collect_failures()
    assert len(failures) > 1
