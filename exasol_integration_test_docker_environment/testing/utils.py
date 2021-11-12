import json
import socket
from contextlib import closing

import requests

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient

INTEGRATION_TEST_DOCKER_ENVIRONMENT_DEFAULT_BIN = "./start-test-env-without-poetry"


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        port = s.getsockname()[1]
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', port))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return port


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
