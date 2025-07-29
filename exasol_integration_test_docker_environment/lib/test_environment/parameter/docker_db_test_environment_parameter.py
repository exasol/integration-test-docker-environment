from enum import (
    Enum,
    auto,
)
from typing import (
    Optional,
)

import luigi
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
    docker_db_image_name: Optional[str] = luigi.OptionalParameter(default=None)
    docker_db_image_version: Optional[str] = luigi.OptionalParameter(default=None)
    reuse_database: bool = luigi.BoolParameter(default=False, significant=False)
    db_os_access = luigi.EnumParameter(
        default=DbOsAccess.DOCKER_EXEC, enum=DbOsAccess, significant=False
    )
    no_database_cleanup_after_success: bool = luigi.BoolParameter(
        default=False, significant=False
    )
    no_database_cleanup_after_failure: bool = luigi.BoolParameter(
        default=False, significant=False
    )
    database_port_forward: Optional[str] = luigi.OptionalParameter(
        default=None, significant=False
    )
    bucketfs_port_forward: Optional[str] = luigi.OptionalParameter(
        default=None, significant=False
    )
    ssh_port_forward: Optional[str] = luigi.OptionalParameter(
        default=None, significant=False
    )
    mem_size: Optional[str] = luigi.OptionalParameter(
        default="2 GiB", significant=False
    )
    disk_size: Optional[str] = luigi.OptionalParameter(
        default="2 GiB", significant=False
    )
    nameservers: list[str] = luigi.ListParameter(default=[], significant=False)
