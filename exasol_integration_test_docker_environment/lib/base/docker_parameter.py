import luigi
from luigi import Config
from luigi.parameter import ParameterVisibility


class DockerParameter(Config):
    """
    Docker parameters used for Tasks accessing Docker client.
    """

    timeout = luigi.IntParameter(
        100000, significant=False, visibility=ParameterVisibility.PRIVATE
    )
    no_cache = luigi.BoolParameter(False)
