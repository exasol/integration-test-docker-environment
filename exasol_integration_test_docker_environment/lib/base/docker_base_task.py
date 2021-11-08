import luigi
from luigi.parameter import ParameterVisibility

from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import DependencyLoggerBaseTask
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient


class DockerBaseTask(DependencyLoggerBaseTask):
    timeout = luigi.IntParameter(100000, significant=False, visibility=ParameterVisibility.PRIVATE)
    no_cache = luigi.BoolParameter(False)

    def _get_docker_client(self):
        return ContextDockerClient(timeout=self.timeout)
