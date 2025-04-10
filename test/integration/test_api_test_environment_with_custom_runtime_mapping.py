from pathlib import Path
from typing import Optional

import pytest

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.models.data.environment_info import (
    EnvironmentInfo,
)
from exasol_integration_test_docker_environment.lib.models.data.test_container_content_description import (
    TestContainerRuntimeMapping,
)
from exasol_integration_test_docker_environment.test.get_test_container_content import (
    get_test_container_content,
)

def _assert_deployment_available(environment_info: EnvironmentInfo) -> None:
    with ContextDockerClient() as docker_client:
        assert environment_info.test_container_info
        test_container = docker_client.containers.get(
            environment_info.test_container_info.container_name
        )
        exit_code, output = test_container.exec_run("cat /test/test.txt")
        assert exit_code == 0
        assert output.decode("utf-8") == "test"

def _assert_deployment_not_shared(
    environment_info: EnvironmentInfo, temp_path: Path
):
    with ContextDockerClient() as docker_client:
        assert environment_info.test_container_info
        test_container = docker_client.containers.get(
            environment_info.test_container_info.container_name
        )
        exit_code, output = test_container.exec_run(
            "touch /test_target/test_new.txt"
        )
        assert exit_code == 0

        local_path = temp_path / "test.txt"
        assert local_path.exists()

        local_path = temp_path / "test_new.txt"
        assert local_path.exists() == False

@pytest.fixture
def make_test_mapping(tmp_path):
    def make(deployment_target: Optional[str] = None):
        with open(tmp_path / "test.txt", "w") as f:
            f.write("test")
        return TestContainerRuntimeMapping(
            source=tmp_path, target="/test", deployment_target=deployment_target
        )
    return make

def test_runtime_mapping_without_deployment(api_database_with_test_container, make_test_mapping):
    mapping = make_test_mapping()
    with api_database_with_test_container(test_container_content=get_test_container_content(runtime_mapping=(mapping,))) as test_environment:
        assert test_environment.environment_info is not None
        _assert_deployment_available(test_environment.environment_info)

def test_runtime_mapping_deployment(api_database_with_test_container, make_test_mapping):
    mapping = make_test_mapping(deployment_target="/test_target")
    with api_database_with_test_container(
            test_container_content=get_test_container_content(runtime_mapping=(mapping,))) as test_environment:
            assert test_environment.environment_info is not None
            _assert_deployment_available(test_environment.environment_info)
            _assert_deployment_not_shared(test_environment.environment_info, mapping.source)

