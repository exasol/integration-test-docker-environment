from pathlib import PurePath
from typing import List

import docker

from exasol_integration_test_docker_environment.lib.base.db_os_executor import (
    DbOsExecutor,
)


def find_exaplus(
    db_container: docker.models.containers.Container,
    os_executor: DbOsExecutor,
) -> PurePath:
    """
    Tries to find path of exaplus in given container in directories where exaplus is normally installed.
    :db_container Container where to search for exaplus
    """
    exit, output = os_executor.exec("find /usr/opt -name 'exaplus' -type f")
    if exit != 0 or output == b"":
        # Using /usr/opt and /opt together in one command doesn't work,
        # because in Exasol 8, /usr/opt doesn't exist
        # and as such the command fails, even if it finds exaplus in /opt
        exit, output = os_executor.exec("find /opt -name 'exaplus' -type f")
    if exit != 0:
        raise RuntimeError(f"Exaplus not found on docker db! Output is {output}")
    found_paths: List[str] = list(filter(None, output.decode("UTF-8").split("\n")))
    if len(found_paths) != 1:
        raise RuntimeError(f"Error determining exaplus path! Output is {output}")
    exaplus_path = PurePath(found_paths[0])
    exit, output = os_executor.exec(f"{exaplus_path} --help")
    if exit != 0:
        raise RuntimeError(f"Exaplus not working as expected! Output is {output}")
    return exaplus_path
