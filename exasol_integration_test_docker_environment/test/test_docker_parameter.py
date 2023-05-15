import luigi
import pytest

from exasol_integration_test_docker_environment.lib.api.common import generate_root_task
from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task \
     import DependencyLoggerBaseTask
from exasol_integration_test_docker_environment.lib.test_environment.parameter.docker_db_test_environment_parameter \
     import DockerAccess, DockerDBTestEnvironmentParameter


class Testee(DependencyLoggerBaseTask, DockerDBTestEnvironmentParameter):
    def run_task(self):
        print(self.docker_access)
        self.logger.error(self.docker_access)

    @classmethod
    def make(cls, method: str) -> 'Testee':
        kwargs={"task_class": Testee}
        if method:
            kwargs["docker_access"] = method
        task = generate_root_task(**kwargs)
        luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
        return task


def test_docker_access_default():
    testee = Testee.make(None)
    assert testee.docker_access == DockerAccess.DOCKER_EXEC


@pytest.mark.parametrize("method", [DockerAccess.DOCKER_EXEC, DockerAccess.SSH])
def test_docker_access_parameter(method):
    testee = Testee.make(method)
    assert testee.docker_access == method


def test_docker_access_invalid_method():
    with pytest.raises(AttributeError) as ex:
        Testee.make("invalid method")
