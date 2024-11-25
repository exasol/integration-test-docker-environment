from typing import Dict, Any

import luigi
import pytest

from exasol_integration_test_docker_environment.lib.api.common import generate_root_task
from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task \
     import DependencyLoggerBaseTask
from exasol_integration_test_docker_environment.lib.test_environment.parameter.docker_db_test_environment_parameter \
     import DbOsAccess, DockerDBTestEnvironmentParameter


class Testee(DependencyLoggerBaseTask, DockerDBTestEnvironmentParameter):
    def run_task(self):
        pass

    @classmethod
    def make(cls, method: str) -> 'Testee':
        kwargs : Dict[str, Any] = {"task_class": Testee}
        if method:
            kwargs["db_os_access"] = method
        task : Testee = generate_root_task(**kwargs) # type: ignore
        luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
        return task


def test_db_os_access_default():
    testee = Testee.make(None)
    assert testee.db_os_access == DbOsAccess.DOCKER_EXEC


@pytest.mark.parametrize("method", [DbOsAccess.DOCKER_EXEC, DbOsAccess.SSH])
def test_db_os_access_parameter(method):
    testee = Testee.make(method)
    assert testee.db_os_access == method


def test_db_os_access_invalid():
    with pytest.raises(AttributeError) as ex:
        Testee.make("invalid method")
