from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import (
    DependencyLoggerBaseTask,
)
from exasol_integration_test_docker_environment.lib.base.docker_parameter import (
    DockerParameter,
)
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient


class DockerBaseTask(DependencyLoggerBaseTask, DockerParameter):

    def _get_docker_client(self):
        return ContextDockerClient(timeout=self.timeout)
