import pytest

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient


def assert_container_runtime(container_name, expected_runtime):
    with ContextDockerClient() as docker_client:
        container = docker_client.containers.get(container_name)
        container.reload()
        actual_runtime = container.attrs["HostConfig"]["Runtime"]
        assert (
            actual_runtime == expected_runtime
        ), f"{container_name} has the wrong runtime expected {expected_runtime} got {actual_runtime}."


@pytest.fixture(scope="module")
def default_docker_runtime():
    with ContextDockerClient() as docker_client:
        tmp_container = docker_client.containers.create("ubuntu:22.04", "echo")
        try:
            tmp_container.reload()
            default_docker_runtime = tmp_container.attrs["HostConfig"]["Runtime"]
        finally:
            tmp_container.remove(force=True)
        return default_docker_runtime
