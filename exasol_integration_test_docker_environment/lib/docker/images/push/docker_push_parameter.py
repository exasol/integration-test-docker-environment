import luigi
from luigi import Config


class DockerPushParameter(Config):
    force_push: bool = luigi.BoolParameter(default=False)
    push_all: bool = luigi.BoolParameter(default=False)
