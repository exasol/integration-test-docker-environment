import shutil
from pathlib import Path

import luigi

from exasol_integration_test_docker_environment.lib.base.run_task import (
    generate_root_task,
)
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.docker.images.create.docker_build_base import (
    DockerBuildBase,
)
from exasol_integration_test_docker_environment.lib.docker.images.create.docker_image_analyze_task import (
    DockerAnalyzeImageTask,
)
from exasol_integration_test_docker_environment.lib.models.config.build_config import (
    set_build_config,
)
from exasol_integration_test_docker_environment.lib.models.config.docker_config import (
    set_docker_repository_config,
)
from exasol_integration_test_docker_environment.testing import luigi_utils
from exasol_integration_test_docker_environment.testing.docker_registry import (
    LocalDockerRegistryContextManager,
)

RESOURCE_ROOT = (
    Path(__file__).resolve().parent / "resources" / "test_external_image_pull_graph"
)
TEST_GRAPH_ROOT: Path | None = None
LOCAL_BUILD_REPOSITORY = "itde-test-external-pull-graph"
EXTERNAL_FROM_REFERENCE = ""
EXTERNAL_COPY_REFERENCE = ""


class BuildStepBaseAnalyzeTask(DockerAnalyzeImageTask):
    def get_source_repository_name(self) -> str:
        return LOCAL_BUILD_REPOSITORY

    def get_target_repository_name(self) -> str:
        return LOCAL_BUILD_REPOSITORY

    def get_source_image_tag(self):
        return "build-step-base"

    def get_target_image_tag(self):
        return "build-step-base"

    def get_mapping_of_build_files_and_directories(self):
        assert TEST_GRAPH_ROOT is not None
        return {
            "build-step-base.txt": str(
                TEST_GRAPH_ROOT / "build_step_base" / "build-step-base.txt"
            ),
        }

    def get_dockerfile(self):
        assert TEST_GRAPH_ROOT is not None
        return str(TEST_GRAPH_ROOT / "build_step_base" / "Dockerfile")

    def is_rebuild_requested(self) -> bool:
        return True


class BuildStepCopySourceAnalyzeTask(DockerAnalyzeImageTask):
    def get_source_repository_name(self) -> str:
        return LOCAL_BUILD_REPOSITORY

    def get_target_repository_name(self) -> str:
        return LOCAL_BUILD_REPOSITORY

    def get_source_image_tag(self):
        return "build-step-copy-source"

    def get_target_image_tag(self):
        return "build-step-copy-source"

    def get_mapping_of_build_files_and_directories(self):
        assert TEST_GRAPH_ROOT is not None
        return {
            "build-step-copy-source.txt": str(
                TEST_GRAPH_ROOT
                / "build_step_copy_source"
                / "build-step-copy-source.txt"
            ),
        }

    def get_dockerfile(self):
        assert TEST_GRAPH_ROOT is not None
        return str(TEST_GRAPH_ROOT / "build_step_copy_source" / "Dockerfile")

    def is_rebuild_requested(self) -> bool:
        return True


class FinalAnalyzeTask(DockerAnalyzeImageTask):
    def get_source_repository_name(self) -> str:
        return LOCAL_BUILD_REPOSITORY

    def get_target_repository_name(self) -> str:
        return LOCAL_BUILD_REPOSITORY

    def get_source_image_tag(self):
        return "final-image"

    def get_target_image_tag(self):
        return "final-image"

    def get_mapping_of_build_files_and_directories(self):
        return {}

    def get_dockerfile(self):
        assert TEST_GRAPH_ROOT is not None
        return str(TEST_GRAPH_ROOT / "final_image" / "Dockerfile")

    def is_rebuild_requested(self) -> bool:
        return True

    def requires_tasks(self) -> dict[str, type[DockerAnalyzeImageTask]]:
        return {
            "build_step_base": BuildStepBaseAnalyzeTask,
            "build_step_copy_source": BuildStepCopySourceAnalyzeTask,
        }


class ExternalImagePullGraphBuild(DockerBuildBase):
    def get_goal_class_map(self) -> dict[str, DockerAnalyzeImageTask]:
        return {
            "final-image": self.create_child_task(FinalAnalyzeTask),
        }

    def get_default_goals(self) -> set[str]:
        return {"final-image"}

    def get_goals(self) -> set[str]:
        return {"final-image"}

    def run_task(self):
        build_tasks = self.create_build_tasks(False)
        image_infos_futures = yield from self.run_dependencies(build_tasks)
        image_infos = self.get_values_from_futures(image_infos_futures)
        self.return_object(image_infos)


def _prepare_graph_workspace(target_root: Path) -> Path:
    workspace = target_root / "external-image-pull-graph"
    shutil.copytree(RESOURCE_ROOT, workspace)
    final_dockerfile = workspace / "final_image" / "Dockerfile"
    final_dockerfile.write_text(
        final_dockerfile.read_text()
        .replace("__EXTERNAL_FROM__", EXTERNAL_FROM_REFERENCE)
        .replace("__EXTERNAL_COPY__", EXTERNAL_COPY_REFERENCE)
    )
    return workspace


def _split_image_reference(image_reference: str) -> tuple[str, str]:
    repository, tag = image_reference.rsplit(":", 1)
    return repository, tag


def _build_and_push_external_image(
    image_directory: Path, local_tag: str, registry_reference: str
) -> None:
    repository, tag = _split_image_reference(registry_reference)
    with ContextDockerClient() as docker_client:
        docker_client.images.build(path=str(image_directory), tag=local_tag, rm=True)
        image = docker_client.images.get(local_tag)
        image.tag(repository=repository, tag=tag)
        docker_client.images.push(repository=repository, tag=tag)
        docker_client.images.remove(local_tag, force=True)
        docker_client.images.remove(registry_reference, force=True)


def _read_marker_file(image_reference: str, marker_path: str) -> str:
    with ContextDockerClient() as docker_client:
        output = docker_client.containers.run(
            image_reference,
            command=["cat", marker_path],
            remove=True,
        )
    return output.decode("utf-8").strip()


def test_external_pull_graph_uses_local_registry_only_for_external_images(
    luigi_output, tmp_path: Path
):
    global TEST_GRAPH_ROOT
    global EXTERNAL_FROM_REFERENCE
    global EXTERNAL_COPY_REFERENCE
    with LocalDockerRegistryContextManager("external-pull-graph") as docker_registry:
        EXTERNAL_FROM_REFERENCE = f"{docker_registry.name}/external-from:1"
        EXTERNAL_COPY_REFERENCE = f"{docker_registry.name}/external-copy:1"
        TEST_GRAPH_ROOT = _prepare_graph_workspace(tmp_path)
        _build_and_push_external_image(
            TEST_GRAPH_ROOT / "external_from",
            "external-pull-graph-local-external-from:1",
            EXTERNAL_FROM_REFERENCE,
        )
        _build_and_push_external_image(
            TEST_GRAPH_ROOT / "external_copy",
            "external-pull-graph-local-external-copy:1",
            EXTERNAL_COPY_REFERENCE,
        )
        set_build_config(
            True,
            (),
            False,
            False,
            str(luigi_output),
            str(tmp_path),
            "",
            "test",
        )
        set_docker_repository_config(None, LOCAL_BUILD_REPOSITORY, None, "", "source")
        set_docker_repository_config(None, LOCAL_BUILD_REPOSITORY, None, "", "target")
        task = generate_root_task(task_class=ExternalImagePullGraphBuild)
        try:
            result = luigi.build(
                [task], workers=3, local_scheduler=True, log_level="INFO"
            )
            assert result
            image_infos = task.get_result()
            final_image_reference = image_infos[
                "final-image"
            ].get_target_complete_name()
            assert (
                _read_marker_file(final_image_reference, "/markers/build-step-base.txt")
                == "build-step-base"
            )
            assert (
                _read_marker_file(
                    final_image_reference, "/markers/build-step-copy-source.txt"
                )
                == "build-step-copy-source"
            )
            assert (
                _read_marker_file(final_image_reference, "/markers/external-from.txt")
                == "external-from"
            )
            assert (
                _read_marker_file(final_image_reference, "/markers/external-copy.txt")
                == "external-copy"
            )
            assert sorted(docker_registry.repositories) == [
                "external-pull-graph/external-copy",
                "external-pull-graph/external-from",
            ]
        finally:
            TEST_GRAPH_ROOT = None
            EXTERNAL_FROM_REFERENCE = ""
            EXTERNAL_COPY_REFERENCE = ""
            luigi_utils.clean(LOCAL_BUILD_REPOSITORY)
