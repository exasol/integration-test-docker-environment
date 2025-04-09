import luigi
from luigi import Config
from luigi.parameter import ParameterVisibility


class DockerParameter(Config):
    """
    Docker parameters used for Tasks accessing Docker client.
    """

    timeout: int = luigi.IntParameter(
        default=100000, significant=False, visibility=ParameterVisibility.PRIVATE
    )
    no_cache: bool = luigi.BoolParameter(default=False)
