from exasol_integration_test_docker_environment.lib.base import luigi_compat as luigi
from exasol_integration_test_docker_environment.lib.base.luigi_compat import (
    Config,
    ParameterVisibility,
)


class DockerParameter(Config):
    """
    Docker parameters used for Tasks accessing Docker client.
    """

    timeout: int = luigi.IntParameter(
        default=100000, significant=False, visibility=ParameterVisibility.PRIVATE
    )
    no_cache: bool = luigi.BoolParameter(default=False)
