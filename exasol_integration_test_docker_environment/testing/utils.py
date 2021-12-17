import json
import os
import socket
from contextlib import ExitStack
from typing import Optional, List

import requests

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient

INTEGRATION_TEST_DOCKER_ENVIRONMENT_DEFAULT_BIN = "./start-test-env-without-poetry"


def find_free_ports(num_ports: int) -> List[int]:

    ret_val = list()
    with ExitStack() as stack:
        sockets = [stack.enter_context(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) for dummy in range(num_ports)]
        for s in sockets:
            s.bind(('', 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            ret_val.append(s.getsockname()[1])
    with ExitStack() as stack:
        # Create an array of tuples of new socket + port to use
        sockets = [(stack.enter_context(socket.socket(socket.AF_INET, socket.SOCK_STREAM)), port) for port in ret_val]
        for socket_port in sockets:
            s = socket_port[0]
            port = socket_port[1]
            s.bind(('', port))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return ret_val


def remove_docker_container(containers):
    with ContextDockerClient() as docker_client:
        for container in containers:
            try:
                docker_client.containers.get(container).remove(force=True)
            except Exception as e:
                print(e)


def remove_docker_volumes(volumes):
    with ContextDockerClient() as docker_client:
        for volume in volumes:
            try:
                docker_client.volumes.get(volume).remove(force=True)
            except Exception as e:
                print(e)


def request_registry_images(registry_host, registry_port, repo_name):
    url = f"http://{registry_host}:{registry_port}/v2/{repo_name}/tags/list"
    result = requests.request("GET", url)
    images = json.loads(result.content.decode("UTF-8"))
    return images


def request_registry_repositories(registry_host, registry_port):
    result = requests.request("GET", f"http://{registry_host}:{registry_port}/v2/_catalog/")
    repositories_ = json.loads(result.content.decode("UTF-8"))["repositories"]
    return repositories_


def close_environments(*args):
    for env in args:
        try:
            if env is not None:
                env.close()
        except Exception as e:
            print(e)


def check_db_version_from_env() -> Optional[str]:
    retval = None
    if "EXASOL_VERSION" in os.environ and os.environ["EXASOL_VERSION"] != "default":
        retval = os.environ["EXASOL_VERSION"]
    return retval


def db_version_supports_custom_certificates(db_version: Optional[str]) -> bool:
    # 1. If db_version is None => Latest DB version is used (which already supported custom certificates in EXAConf
    # 2. If db_version is "default" => Return True, as "default" is lexically greater than "7.0.5"
    # 3. Return result of db version comparison
    return True if db_version is None or db_version > "7.0.5" else False
