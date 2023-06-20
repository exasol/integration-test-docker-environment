import luigi
from enum import Enum, auto
from luigi import Config

class DbOsAccess(Enum):
    """
    This enum represents different methods to access the operating system
    of the Docker Container running the Exasol database.

    The Docker Container of older database versions allowed to use
    ``docker_exec`` as well, while newer versions require SSH.

    Currently the SSH access is not implemented fully but the current test
    case will verify that when using SSH access a file with the required
    private key is generated.
    """
    DOCKER_EXEC = auto()
    SSH = auto()


class DockerDBTestEnvironmentParameter(Config):
    docker_db_image_name = luigi.OptionalParameter(None)
    docker_db_image_version = luigi.OptionalParameter(None)
    reuse_database = luigi.BoolParameter(False, significant=False)
    db_os_access = luigi.EnumParameter(DbOsAccess.DOCKER_EXEC, enum=DbOsAccess, significant=False)
    no_database_cleanup_after_success = luigi.BoolParameter(False, significant=False)
    no_database_cleanup_after_failure = luigi.BoolParameter(False, significant=False)
    database_port_forward = luigi.OptionalParameter(None, significant=False)
    bucketfs_port_forward = luigi.OptionalParameter(None, significant=False)
    ssh_port_forward = luigi.OptionalParameter(None, significant=False)
    mem_size = luigi.OptionalParameter("2 GiB", significant=False)
    disk_size = luigi.OptionalParameter("2 GiB", significant=False)
    nameservers = luigi.ListParameter([], significant=False)
