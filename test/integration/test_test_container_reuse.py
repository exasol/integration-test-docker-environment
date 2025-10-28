import shutil
from pathlib import Path

import luigi
import pytest

from exasol_integration_test_docker_environment.lib.base.docker_base_task import (
    DockerBaseTask,
)
from exasol_integration_test_docker_environment.lib.base.run_task import (
    generate_root_task,
)
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.models.config.build_config import (
    set_build_config,
)
from exasol_integration_test_docker_environment.lib.models.config.docker_config import (
    set_docker_repository_config,
)
from exasol_integration_test_docker_environment.lib.models.data.container_info import (
    ContainerInfo,
)
from exasol_integration_test_docker_environment.lib.models.data.test_container_content_description import (
    TestContainerContentDescription,
)
from exasol_integration_test_docker_environment.lib.test_environment.parameter.test_container_parameter import (
    TestContainerParameter,
)
from exasol_integration_test_docker_environment.lib.test_environment.prepare_network_for_test_environment import (
    PrepareDockerNetworkForTestEnvironment,
)
from exasol_integration_test_docker_environment.lib.test_environment.spawn_test_container import (
    SpawnTestContainer,
)
from exasol_integration_test_docker_environment.test.get_test_container_content import (
    TEST_CONTAINER_REUSE_ROOT_PATH,
)
from exasol_integration_test_docker_environment.testing import luigi_utils


class TestTask(DockerBaseTask, TestContainerParameter):
    reuse = luigi.BoolParameter()
    attempt = luigi.IntParameter()

    def run_task(self):
        docker_network_task_1 = self.create_child_task(
            task_class=PrepareDockerNetworkForTestEnvironment,
            environment_name="test_environment_TestContainerReuseTest",
            network_name="docker_network_TestContainerReuseTest",
            test_container_name="test_container_TestContainerReuseTest",
            db_container_name="db_container_TestContainerReuseTest",
            reuse=self.reuse,
            no_cleanup_after_success=True,
            no_cleanup_after_failure=False,
            attempt=self.attempt,
        )
        self.docker_network_future_1 = yield from self.run_dependencies(
            docker_network_task_1
        )

        test_container_task_1 = self.create_child_task(
            task_class=SpawnTestContainer,
            environment_name="test_environment_TestContainerReuseTest",
            test_container_name="test_container_TestContainerReuseTest",
            network_info=self.docker_network_future_1.get_output(),
            ip_address_index_in_subnet=2,
            attempt=self.attempt,
            reuse_test_container=self.reuse,
            no_test_container_cleanup_after_success=True,
            no_test_container_cleanup_after_failure=False,
            test_container_content=self.test_container_content,
        )
        test_container_future_1 = yield from self.run_dependencies(
            test_container_task_1
        )
        container_info: ContainerInfo = test_container_future_1.get_output()  # type: ignore
        with ContextDockerClient() as docker_client:
            container = docker_client.containers.get(container_info.container_name)
            self.return_object(
                {"container_id": container.id, "image_id": container.image.id}
            )


def _setup_luigi_config(output_directory: Path, docker_repository_name: str):
    set_build_config(
        force_rebuild=False,
        force_pull=False,
        force_rebuild_from=(),
        log_build_context_content=False,
        output_directory=str(output_directory),
        cache_directory="",
        build_name="",
        temporary_base_directory="/tmp",
    )
    set_docker_repository_config(
        docker_password=None,
        docker_repository_name=docker_repository_name,
        docker_username=None,
        tag_prefix="",
        kind="target",
    )


@pytest.fixture
def working_directory(tmp_path_factory):
    resource_directory = TEST_CONTAINER_REUSE_ROOT_PATH

    temp_directory = tmp_path_factory.mktemp("container")
    output_directory = tmp_path_factory.mktemp("output")
    working_directory = shutil.copytree(
        resource_directory, temp_directory / "test_test_container_reuse"
    )
    docker_repository_name = "test_test_container_reuse"
    _setup_luigi_config(
        output_directory=output_directory, docker_repository_name=docker_repository_name
    )
    luigi_utils.clean(docker_repository_name)
    yield working_directory
    luigi_utils.clean(docker_repository_name)


def _dockerfile(working_directory: Path):
    return working_directory / "tests" / "Dockerfile"


def _get_test_container_content(
    working_directory: Path,
) -> TestContainerContentDescription:
    return TestContainerContentDescription(
        docker_file=str(_dockerfile(working_directory)),
        build_files_and_directories=[],
        runtime_mappings=[],
    )


def run1(working_directory: Path):
    task = generate_root_task(
        task_class=TestTask,
        reuse=False,
        attempt=1,
        test_container_content=_get_test_container_content(working_directory),
    )
    try:
        success = luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
        if success:
            result = task.get_result()
            task.cleanup(True)
            return result
        else:
            raise Exception("Task failed")
    except Exception as e:
        task.cleanup(False)
        raise RuntimeError("Error spawning test environment") from e


def run2(working_directory: Path):
    task = generate_root_task(
        task_class=TestTask,
        reuse=True,
        attempt=2,
        test_container_content=_get_test_container_content(working_directory),
    )
    try:
        success = luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")

        if success:
            return task.get_result()
        else:
            raise Exception("Task failed")
    except Exception as e:
        task.cleanup(False)
        raise RuntimeError("Error spawning test environment") from e


def test_test_container_no_reuse_after_change(working_directory):
    p1 = run1(working_directory)
    with _dockerfile(working_directory).open("a") as f:
        f.write("\n#Test\n")
    p2 = run2(working_directory)
    assert "container_id" in p1
    assert "image_id" in p1
    assert "container_id" in p2
    assert "image_id" in p2
    print(p1)
    print(p2)
    assert p1 != p2


def test_test_container_reuse(working_directory):
    p1 = run1(working_directory)
    p2 = run2(working_directory)
    assert "container_id" in p1
    assert "image_id" in p1
    print(p1)
    print(p2)
    assert p1 == p2
