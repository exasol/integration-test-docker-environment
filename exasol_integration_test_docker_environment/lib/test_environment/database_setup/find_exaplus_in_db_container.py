from pathlib import PurePath

import docker.models.containers


def find_exaplus(db_container: docker.models.containers.Container) -> PurePath:
    """
    Tries to find path of exaplus in given container in directories where exaplus is normally installed.
    :db_container Container where to search for exaplus
    """
    exit, output = db_container.exec_run(cmd="find /usr/opt /opt  -name 'exaplus' -type f")
    if exit != 0:
        raise RuntimeError(f"Exaplus not found on docker db! Output is {output}")
    found_paths = list(filter(None, output.decode("UTF-8").split("\n")))
    if len(found_paths) != 1:
        raise RuntimeError(f"Error determining exaplus path! Output is {output}")
    exaplus_path = PurePath(found_paths[0])
    exit, output = db_container.exec_run(cmd=f"{exaplus_path} --help")
    if exit != 0:
        raise RuntimeError(f"Exaplus not working as expected! Output is {output}")
    return exaplus_path
