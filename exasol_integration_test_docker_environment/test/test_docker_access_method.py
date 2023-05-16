import luigi
import pytest

from exasol_integration_test_docker_environment.lib.api.common import generate_root_task
from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task \
     import DependencyLoggerBaseTask
from exasol_integration_test_docker_environment.lib.test_environment.parameter.docker_db_test_environment_parameter \
     import DockerAccessMethod, DockerDBTestEnvironmentParameter


class Testee(DependencyLoggerBaseTask, DockerDBTestEnvironmentParameter):
    def run_task(self):
        print(self.docker_access_method)
        self.logger.error(self.docker_access_method)

    @classmethod
    def make(cls, method: str) -> 'Testee':
        kwargs={"task_class": Testee}
        if method:
            kwargs["docker_access_method"] = method
        task = generate_root_task(**kwargs)
        luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
        return task


def test_docker_access_method_default():
    testee = Testee.make(None)
    assert testee.docker_access_method == DockerAccessMethod.DOCKER_EXEC


@pytest.mark.parametrize("method", [DockerAccessMethod.DOCKER_EXEC, DockerAccessMethod.SSH])
def test_docker_access_method_parameter(method):
    testee = Testee.make(method)
    assert testee.docker_access_method == method


def test_docker_access_method_invalid():
    with pytest.raises(AttributeError) as ex:
        Testee.make("invalid method")
