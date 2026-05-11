from exasol_integration_test_docker_environment.lib.base import luigi_compat as luigi
from exasol_integration_test_docker_environment.lib.base.luigi_compat import Config


class DockerPushParameter(Config):
    force_push: bool = luigi.BoolParameter(default=False)
    push_all: bool = luigi.BoolParameter(default=False)
