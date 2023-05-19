import luigi
import enum import Enum, auto
from luigi import Config

class DockerAccessMethod(Enum):
     DOCKER_EXEC = auto()
     SSH = auto()


class DockerDBTestEnvironmentParameter(Config):
    docker_db_image_name = luigi.OptionalParameter(None)
    docker_db_image_version = luigi.OptionalParameter(None)
    reuse_database = luigi.BoolParameter(False, significant=False)
    docker_access_method = luigi.EnumParameter(DockerAccessMethod.DOCKER_EXEC, enum=DockerAccessMethod, significant=False)
    no_database_cleanup_after_success = luigi.BoolParameter(False, significant=False)
    no_database_cleanup_after_failure = luigi.BoolParameter(False, significant=False)
    database_port_forward = luigi.OptionalParameter(None, significant=False)
    bucketfs_port_forward = luigi.OptionalParameter(None, significant=False)
    mem_size = luigi.OptionalParameter("2 GiB", significant=False)
    disk_size = luigi.OptionalParameter("2 GiB", significant=False)
    nameservers = luigi.ListParameter([], significant=False)
