import multiprocessing
import sys
from pathlib import Path
from unittest.mock import Mock

import docker
import luigi
import pytest

from exasol_integration_test_docker_environment.lib.base.run_task import (
    generate_root_task,
)
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
from test.integration.test_external_image_pull_graph import (
    _is_image_available_locally,
    _mirror_image_to_registry,
)

TEST_GRAPH_ROOT: Path | None = None
TEST_EXTERNAL_FROM_REFERENCE = "registry.local/test/external-from:1"
TEST_EXTERNAL_COPY_REFERENCE = "registry.local/test/external-copy:1"


@pytest.fixture
def luigi_output(tmp_path: Path):
    if sys.platform != "win32":
        multiprocessing.set_start_method("fork", force=True)
    set_build_config(
        True,
        (),
        False,
        False,
        str(tmp_path),
        str(tmp_path.parent),
        "",
        "test",
    )
    return tmp_path


class _FakeImages:
    def __init__(self, backend) -> None:
        self._backend = backend

    def get(self, image_reference: str):
        if image_reference not in self._backend.local_images:
            raise docker.errors.ImageNotFound(f"image {image_reference} not available")
        return object()

    def pull(self, repository: str, tag: str | None = None, auth_config=None):
        image_reference = repository if tag in (None, "") else f"{repository}:{tag}"
        self._backend.pull_calls.append(image_reference)
        self._backend.local_images[image_reference] = True
        return object()


class _FakeApi:
    def __init__(self, backend) -> None:
        self._backend = backend

    def build(
        self, path: str, nocache: bool, tag: str, rm: bool, buildargs, pull: bool
    ):
        self._backend.build_calls.append({"tag": tag, "pull": pull, "path": path})
        self._backend.local_images[tag] = True
        return [b'{"stream":"Successfully built"}']


class _FakeDockerClient:
    def __init__(self, backend) -> None:
        self.images = _FakeImages(backend)
        self.api = _FakeApi(backend)

    def close(self):
        pass


class _FakeDockerBackend:
    def __init__(self) -> None:
        self._manager = multiprocessing.Manager()
        self.local_images = self._manager.dict()
        self.pull_calls = self._manager.list()
        self.build_calls = self._manager.list()

    def create_context_manager(self, **kwargs):
        backend = self

        class _FakeContextManager:
            def __enter__(self_nonlocal):
                return _FakeDockerClient(backend)

            def __exit__(self_nonlocal, exc_type, exc_val, exc_tb):
                return False

        return _FakeContextManager()


class BuildStepBaseAnalyzeTask(DockerAnalyzeImageTask):
    def get_source_repository_name(self) -> str:
        return "mocked/repository"

    def get_target_repository_name(self) -> str:
        return "mocked/repository"

    def get_source_image_tag(self):
        return "build-step-base"

    def get_target_image_tag(self):
        return "build-step-base"

    def get_mapping_of_build_files_and_directories(self):
        assert TEST_GRAPH_ROOT is not None
        return {
            "build-step-base.txt": str(TEST_GRAPH_ROOT / "build-step-base.txt"),
        }

    def get_dockerfile(self):
        assert TEST_GRAPH_ROOT is not None
        return str(TEST_GRAPH_ROOT / "build_step_base.Dockerfile")

    def is_rebuild_requested(self) -> bool:
        return True


class BuildStepCopySourceAnalyzeTask(DockerAnalyzeImageTask):
    def get_source_repository_name(self) -> str:
        return "mocked/repository"

    def get_target_repository_name(self) -> str:
        return "mocked/repository"

    def get_source_image_tag(self):
        return "build-step-copy-source"

    def get_target_image_tag(self):
        return "build-step-copy-source"

    def get_mapping_of_build_files_and_directories(self):
        assert TEST_GRAPH_ROOT is not None
        return {
            "build-step-copy-source.txt": str(
                TEST_GRAPH_ROOT / "build-step-copy-source.txt"
            ),
        }

    def get_dockerfile(self):
        assert TEST_GRAPH_ROOT is not None
        return str(TEST_GRAPH_ROOT / "build_step_copy_source.Dockerfile")

    def is_rebuild_requested(self) -> bool:
        return True


class FinalAnalyzeTask(DockerAnalyzeImageTask):
    def get_source_repository_name(self) -> str:
        return "mocked/repository"

    def get_target_repository_name(self) -> str:
        return "mocked/repository"

    def get_source_image_tag(self):
        return "final-image"

    def get_target_image_tag(self):
        return "final-image"

    def get_mapping_of_build_files_and_directories(self):
        return {}

    def get_dockerfile(self):
        assert TEST_GRAPH_ROOT is not None
        return str(TEST_GRAPH_ROOT / "final.Dockerfile")

    def is_rebuild_requested(self) -> bool:
        return True

    def requires_tasks(self) -> dict[str, type[DockerAnalyzeImageTask]]:
        return {
            "build_step_base": BuildStepBaseAnalyzeTask,
            "build_step_copy_source": BuildStepCopySourceAnalyzeTask,
        }


class MockedDockerBuildRootTask(DockerBuildBase):
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


def _write_test_graph_files(root: Path) -> None:
    (root / "build_step_base.Dockerfile").write_text(
        "FROM scratch\nCOPY build-step-base.txt /markers/build-step-base.txt\n"
    )
    (root / "build-step-base.txt").write_text("build-step-base\n")
    (root / "build_step_copy_source.Dockerfile").write_text(
        "FROM scratch\nCOPY build-step-copy-source.txt /markers/build-step-copy-source.txt\n"
    )
    (root / "build-step-copy-source.txt").write_text("build-step-copy-source\n")
    (root / "final.Dockerfile").write_text(
        "\n".join(
            [
                "FROM {{ build_step_base }} AS local_base",
                f"FROM {TEST_EXTERNAL_FROM_REFERENCE} AS external_from",
                "FROM local_base",
                "COPY --from={{ build_step_copy_source }} /markers/build-step-copy-source.txt /markers/build-step-copy-source.txt",
                "COPY --from=external_from /markers/external-from.txt /markers/external-from.txt",
                f"COPY --from={TEST_EXTERNAL_COPY_REFERENCE} /markers/external-copy.txt /markers/external-copy.txt",
            ]
        )
    )


def test_build_schedules_only_external_pulls(monkeypatch, luigi_output, tmp_path: Path):
    global TEST_GRAPH_ROOT
    TEST_GRAPH_ROOT = tmp_path
    _write_test_graph_files(tmp_path)
    backend = _FakeDockerBackend()

    def _context_factory(**kwargs):
        return backend.create_context_manager(**kwargs)

    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.base.docker_base_task.ContextDockerClient",
        _context_factory,
    )
    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.docker.images.create.utils.docker_image_target.ContextDockerClient",
        _context_factory,
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
    set_docker_repository_config(None, "mocked/repository", None, "", "source")
    set_docker_repository_config(None, "mocked/repository", None, "", "target")
    task = generate_root_task(task_class=MockedDockerBuildRootTask)

    try:
        result = luigi.build([task], workers=2, local_scheduler=True, log_level="INFO")
        assert result
        assert list(backend.pull_calls) == [
            TEST_EXTERNAL_FROM_REFERENCE,
            TEST_EXTERNAL_COPY_REFERENCE,
        ]
        build_calls = list(backend.build_calls)
        assert all(call["pull"] is False for call in build_calls)
        assert len(build_calls) == 3
        built_tags = {call["tag"] for call in build_calls}
        assert any("build-step-base" in tag for tag in built_tags)
        assert any("build-step-copy-source" in tag for tag in built_tags)
        assert any("final-image" in tag for tag in built_tags)
    finally:
        TEST_GRAPH_ROOT = None


def test_mirror_image_to_registry_pulls_pushes_and_clears_local_cache(monkeypatch):
    image_reference = "busybox:1.36.1"
    registry_reference = "registry.local/test/busybox:1.36.1"
    image = Mock()
    docker_client = Mock()
    docker_client.images.get.return_value = image

    class _ContextManager:
        def __enter__(self):
            return docker_client

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

    monkeypatch.setattr(
        "test.integration.test_external_image_pull_graph.ContextDockerClient",
        lambda: _ContextManager(),
    )

    _mirror_image_to_registry(image_reference, registry_reference)

    docker_client.images.pull.assert_called_once_with("busybox", "1.36.1")
    docker_client.images.get.assert_called_once_with(image_reference)
    image.tag.assert_called_once_with(
        repository="registry.local/test/busybox",
        tag="1.36.1",
    )
    docker_client.images.push.assert_called_once_with(
        repository="registry.local/test/busybox",
        tag="1.36.1",
    )
    docker_client.images.remove.assert_any_call(image_reference, force=True)
    docker_client.images.remove.assert_any_call(registry_reference, force=True)


def test_is_image_available_locally_returns_false_for_missing_image(monkeypatch):
    docker_client = Mock()
    docker_client.images.get.side_effect = docker.errors.ImageNotFound("missing")

    class _ContextManager:
        def __enter__(self):
            return docker_client

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

    monkeypatch.setattr(
        "test.integration.test_external_image_pull_graph.ContextDockerClient",
        lambda: _ContextManager(),
    )

    assert _is_image_available_locally("busybox:1.36.1") is False


def test_is_image_available_locally_returns_true_for_present_image(monkeypatch):
    docker_client = Mock()

    class _ContextManager:
        def __enter__(self):
            return docker_client

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

    monkeypatch.setattr(
        "test.integration.test_external_image_pull_graph.ContextDockerClient",
        lambda: _ContextManager(),
    )

    assert _is_image_available_locally("busybox:1.36.1") is True
    docker_client.images.get.assert_called_once_with("busybox:1.36.1")
