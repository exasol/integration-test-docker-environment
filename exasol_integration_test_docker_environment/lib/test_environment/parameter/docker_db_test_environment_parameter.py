from enum import (
    Enum,
    auto,
)
from typing import (
    List,
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
    docker_db_image_name: Optional[str] = luigi.OptionalParameter(None)  # type: ignore
    docker_db_image_version: Optional[str] = luigi.OptionalParameter(None)  # type: ignore
    reuse_database: bool = luigi.BoolParameter(False, significant=False)  # type: ignore
    db_os_access = luigi.EnumParameter(
        DbOsAccess.DOCKER_EXEC, enum=DbOsAccess, significant=False
    )
    no_database_cleanup_after_success: bool = luigi.BoolParameter(False, significant=False)  # type: ignore
    no_database_cleanup_after_failure: bool = luigi.BoolParameter(False, significant=False)  # type: ignore
    database_port_forward: Optional[str] = luigi.OptionalParameter(None, significant=False)  # type: ignore
    bucketfs_port_forward: Optional[str] = luigi.OptionalParameter(None, significant=False)  # type: ignore
    ssh_port_forward: Optional[str] = luigi.OptionalParameter(None, significant=False)  # type: ignore
    mem_size: Optional[str] = luigi.OptionalParameter("2 GiB", significant=False)  # type: ignore
    disk_size: Optional[str] = luigi.OptionalParameter("2 GiB", significant=False)  # type: ignore
    nameservers: List[str] = luigi.ListParameter([], significant=False)  # type: ignore
