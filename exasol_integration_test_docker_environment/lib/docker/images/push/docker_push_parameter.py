import luigi
from luigi import Config


class DockerPushParameter(Config):
    force_push: bool = luigi.BoolParameter(False)  # type: ignore
    push_all: bool = luigi.BoolParameter(False)  # type: ignore
