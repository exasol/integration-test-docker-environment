from test.integration.base_task.base_task import BaseTestTask

import luigi

from exasol_integration_test_docker_environment.lib.base.run_task import (
    generate_root_task,
)


class RootTestTask(BaseTestTask):

    def run_task(self):
        yield from self.run_dependencies(
            [ChildTestTaskWithException(), OtherChildTestTask()]
        )


class ChildTestTaskWithException(BaseTestTask):

    def run_task(self):
        raise Exception()


class OtherChildTestTask(BaseTestTask):

    def run_task(self):
        pass


def test_failing_task(luigi_output):
    task = generate_root_task(task_class=RootTestTask)
    result = luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
    assert not result
