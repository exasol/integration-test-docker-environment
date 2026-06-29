import shutil
from pathlib import Path

import docker
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
LOCAL_BUILD_REPOSITORY = "itde-test-external-pull-graph"
BUSYBOX_REFERENCE = "busybox:1.36.1"


class ExternalImageGraphTaskMixin:
    graph_root: str = luigi.Parameter()
    local_build_repository: str = luigi.Parameter()

    @property
    def graph_root_path(self) -> Path:
        return Path(self.graph_root)


class BuildStepBaseAnalyzeTask(ExternalImageGraphTaskMixin, DockerAnalyzeImageTask):
    def get_source_repository_name(self) -> str:
        return self.local_build_repository

    def get_target_repository_name(self) -> str:
        return self.local_build_repository

    def get_source_image_tag(self):
        return "build-step-base"

    def get_target_image_tag(self):
        return "build-step-base"

    def get_mapping_of_build_files_and_directories(self):
        return {
            "build-step-base.txt": str(
                self.graph_root_path / "build_step_base" / "build-step-base.txt"
            ),
        }

    def get_dockerfile(self):
        return str(self.graph_root_path / "build_step_base" / "Dockerfile")

    def is_rebuild_requested(self) -> bool:
        return True


class BuildStepCopySourceAnalyzeTask(
    ExternalImageGraphTaskMixin, DockerAnalyzeImageTask
):
    def get_source_repository_name(self) -> str:
        return self.local_build_repository

    def get_target_repository_name(self) -> str:
        return self.local_build_repository

    def get_source_image_tag(self):
        return "build-step-copy-source"

    def get_target_image_tag(self):
        return "build-step-copy-source"

    def get_mapping_of_build_files_and_directories(self):
        return {
            "build-step-copy-source.txt": str(
                self.graph_root_path
                / "build_step_copy_source"
                / "build-step-copy-source.txt"
            ),
        }

    def get_dockerfile(self):
        return str(self.graph_root_path / "build_step_copy_source" / "Dockerfile")

    def is_rebuild_requested(self) -> bool:
        return True


class FinalAnalyzeTask(ExternalImageGraphTaskMixin, DockerAnalyzeImageTask):
    def get_source_repository_name(self) -> str:
        return self.local_build_repository

    def get_target_repository_name(self) -> str:
        return self.local_build_repository

    def get_source_image_tag(self):
        return "final-image"

    def get_target_image_tag(self):
        return "final-image"

    def get_mapping_of_build_files_and_directories(self):
        return {}

    def get_dockerfile(self):
        return str(self.graph_root_path / "final_image" / "Dockerfile")

    def is_rebuild_requested(self) -> bool:
        return True

    def requires_tasks(self) -> dict[str, type[DockerAnalyzeImageTask]]:
        return {
            "build_step_base": BuildStepBaseAnalyzeTask,
            "build_step_copy_source": BuildStepCopySourceAnalyzeTask,
        }


class ExternalImagePullGraphBuild(DockerBuildBase):
    graph_root: str = luigi.Parameter()
    local_build_repository: str = luigi.Parameter(default=LOCAL_BUILD_REPOSITORY)

    def get_goal_class_map(self) -> dict[str, DockerAnalyzeImageTask]:
        return {
            "final-image": self.create_child_task(
                FinalAnalyzeTask,
                graph_root=self.graph_root,
                local_build_repository=self.local_build_repository,
            ),
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


def _prepare_graph_workspace_with_references(
    target_root: Path,
    local_busybox_reference: str,
    external_from_reference: str,
    external_copy_reference: str,
) -> Path:
    workspace = target_root / "external-image-pull-graph"
    shutil.copytree(RESOURCE_ROOT, workspace)
    for dockerfile in workspace.rglob("Dockerfile"):
        dockerfile.write_text(
            dockerfile.read_text()
            .replace("__BUSYBOX__", local_busybox_reference)
            .replace("__EXTERNAL_FROM__", external_from_reference)
            .replace("__EXTERNAL_COPY__", external_copy_reference)
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


def _mirror_image_to_registry(image_reference: str, registry_reference: str) -> None:
    repository, tag = _split_image_reference(registry_reference)
    with ContextDockerClient() as docker_client:
        docker_client.images.pull(*_split_image_reference(image_reference))
        image = docker_client.images.get(image_reference)
        image.tag(repository=repository, tag=tag)
        docker_client.images.push(repository=repository, tag=tag)
        docker_client.images.remove(image_reference, force=True)
        docker_client.images.remove(registry_reference, force=True)


def _is_image_available_locally(image_reference: str) -> bool:
    with ContextDockerClient() as docker_client:
        try:
            docker_client.images.get(image_reference)
        except docker.errors.ImageNotFound:
            return False
    return True


def _read_marker_file(image_reference: str, marker_path: str) -> str:
    with ContextDockerClient() as docker_client:
        output = docker_client.containers.run(
            image_reference,
            command=["cat", marker_path],
            remove=True,
        )
    return output.decode("utf-8").strip()


def test_external_pull_graph_builds_mixed_local_and_external_image_references(
    luigi_output, tmp_path: Path
):
    with LocalDockerRegistryContextManager("external-pull-graph") as docker_registry:
        local_busybox_reference = f"{docker_registry.name}/busybox:1.36.1"
        external_from_reference = f"{docker_registry.name}/external-from:1"
        external_copy_reference = f"{docker_registry.name}/external-copy:1"
        _mirror_image_to_registry(BUSYBOX_REFERENCE, local_busybox_reference)
        assert not _is_image_available_locally(BUSYBOX_REFERENCE)
        assert not _is_image_available_locally(local_busybox_reference)
        test_graph_root = _prepare_graph_workspace_with_references(
            tmp_path,
            local_busybox_reference,
            external_from_reference,
            external_copy_reference,
        )
        _build_and_push_external_image(
            test_graph_root / "external_from",
            "external-pull-graph-local-external-from:1",
            external_from_reference,
        )
        _build_and_push_external_image(
            test_graph_root / "external_copy",
            "external-pull-graph-local-external-copy:1",
            external_copy_reference,
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
        task = generate_root_task(
            task_class=ExternalImagePullGraphBuild,
            graph_root=str(test_graph_root),
            local_build_repository=LOCAL_BUILD_REPOSITORY,
        )
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
                "external-pull-graph/busybox",
                "external-pull-graph/external-copy",
                "external-pull-graph/external-from",
            ]
        finally:
            luigi_utils.clean(LOCAL_BUILD_REPOSITORY)
