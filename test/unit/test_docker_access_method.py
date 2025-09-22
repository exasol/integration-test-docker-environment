from typing import (
    Any,
)

import luigi
import pytest

from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import (
    DependencyLoggerBaseTask,
)
from exasol_integration_test_docker_environment.lib.base.run_task import (
    generate_root_task,
)
from exasol_integration_test_docker_environment.lib.test_environment.parameter.docker_db_test_environment_parameter import (
    DbOsAccess,
    DockerDBTestEnvironmentParameter,
)


class MockTask(DependencyLoggerBaseTask, DockerDBTestEnvironmentParameter):

    def run_task(self):
        pass


@pytest.fixture()
def  mock_test_task_creator():

    def make(method: DbOsAccess | None | str) -> MockTask:
        kwargs: dict[str, Any] = {"task_class": MockTask}
        if method:
            kwargs["db_os_access"] = method
        task: Testee = generate_root_task(**kwargs)  # type: ignore
        luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
        return task

    return make


def test_db_os_access_default( mock_test_task_creator):
    testee =  mock_test_task_creator(None)
    assert testee.db_os_access == DbOsAccess.DOCKER_EXEC


@pytest.mark.parametrize("method", [DbOsAccess.DOCKER_EXEC, DbOsAccess.SSH])
def test_db_os_access_parameter( mock_test_task_creator, method):
    testee =  mock_test_task_creator(method)
    assert testee.db_os_access == method


def test_db_os_access_invalid( mock_test_task_creator):
    with pytest.raises(AttributeError) as ex:
         mock_test_task_creator("invalid method")
