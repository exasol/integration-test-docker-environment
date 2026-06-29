from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from exasol_integration_test_docker_environment.lib.docker.images.create.utils.build_context_creator import (
    BuildContextCreator,
)
from exasol_integration_test_docker_environment.lib.docker.images.create.utils.dockerfile_renderer import (
    render_dockerfile_content,
)
from exasol_integration_test_docker_environment.lib.docker.images.image_info import (
    ImageDescription,
    ImageInfo,
    ImageState,
    Platform,
)


@pytest.fixture(autouse=True)
def _mock_current_platform(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.docker.images.image_info.current_platform",
        lambda: Platform.X64,
    )


def _create_dependency_image_info(repository: str, tag: str) -> ImageInfo:
    return ImageInfo(
        source_repository_name=repository,
        target_repository_name=repository,
        source_tag=tag,
        target_tag=tag,
        hash_value="HASH",
        commit="commit",
        image_description=None,
        build_name="build",
        build_date_time=datetime.utcnow(),
        image_state=ImageState.WAS_BUILD,
        depends_on_images={},
        platform=Platform.X64,
    )


def _create_image_info(
    dockerfile: Path,
    build_mapping: dict[str, str],
    additional_resources: dict[str, str] | None = None,
    depends_on_images: dict[str, ImageInfo] | None = None,
) -> ImageInfo:
    return ImageInfo(
        source_repository_name="source/repo",
        target_repository_name="target/repo",
        source_tag="source-tag",
        target_tag="target-tag",
        hash_value="HASH",
        commit="commit",
        image_description=ImageDescription(
            dockerfile=str(dockerfile),
            image_changing_build_arguments={},
            transparent_build_arguments={},
            mapping_of_build_files_and_directories=build_mapping,
            additional_resources=additional_resources or {},
        ),
        build_name="build",
        build_date_time=datetime.utcnow(),
        image_state=ImageState.NEEDS_TO_BE_BUILD,
        depends_on_images=depends_on_images or {},
        platform=Platform.X64,
    )


def test_render_dockerfile_content_without_dependencies(tmp_path: Path):
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM scratch\nCOPY file.txt /file.txt\n")
    image_info = _create_image_info(dockerfile, {})

    assert (
        render_dockerfile_content(image_info) == "FROM scratch\nCOPY file.txt /file.txt"
    )


def test_render_dockerfile_content_with_dependency_placeholder(tmp_path: Path):
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM {{ build_step_base }}\n")
    image_info = _create_image_info(
        dockerfile,
        {},
        depends_on_images={
            "build_step_base": _create_dependency_image_info(
                "dependency/repo", "dependency-tag"
            )
        },
    )

    rendered = render_dockerfile_content(image_info)

    assert rendered == "FROM dependency/repo:dependency-tag_x64_build"


def test_render_dockerfile_content_requires_image_description():
    image_info = _create_dependency_image_info("dependency/repo", "dependency-tag")
    image_info.image_description = None

    with pytest.raises(
        ValueError, match="image_info.image_description must not be None"
    ):
        render_dockerfile_content(image_info)


def test_prepare_build_context_creates_files_and_updates_image_info(tmp_path: Path):
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM {{ build_step_base }}\nCOPY data.txt /data.txt\n")
    source_file = tmp_path / "data.txt"
    source_file.write_text("payload")
    image_info = _create_image_info(
        dockerfile,
        {"data.txt": str(source_file)},
        additional_resources={"config.txt": "config"},
        depends_on_images={
            "build_step_base": _create_dependency_image_info(
                "dependency/repo", "dependency-tag"
            )
        },
    )
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    creator = BuildContextCreator(str(build_dir), image_info, log_dir)
    creator.prepare_build_context_to_temp_dir()

    assert (build_dir / "data.txt").read_text() == "payload"
    assert (build_dir / "config.txt").read_text() == "config"
    generated_dockerfile = (build_dir / "Dockerfile").read_text()
    assert "FROM dependency/repo:dependency-tag_x64_build" in generated_dockerfile
    assert "COPY image_info /build_info/image_info/target-tag" in generated_dockerfile
    assert image_info.image_state == ImageState.WAS_BUILD.name
    stored_image_info = (build_dir / "image_info").read_text()
    assert '"target_tag": "target-tag"' in stored_image_info


def test_prepare_build_context_copies_directory_mapping(tmp_path: Path):
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM scratch\n")
    source_dir = tmp_path / "source_dir"
    source_dir.mkdir()
    (source_dir / "nested.txt").write_text("nested payload")
    image_info = _create_image_info(
        dockerfile,
        {"copied_dir": str(source_dir)},
    )
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    BuildContextCreator(
        str(build_dir), image_info, log_dir
    ).prepare_build_context_to_temp_dir()

    assert (build_dir / "copied_dir" / "nested.txt").read_text() == "nested payload"


def test_prepare_build_context_raises_for_invalid_mapping_source(tmp_path: Path):
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM scratch\n")
    image_info = _create_image_info(
        dockerfile,
        {"missing.txt": str(tmp_path / "does-not-exist.txt")},
    )
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    with pytest.raises(Exception, match="neither a file or a directory"):
        BuildContextCreator(
            str(build_dir), image_info, log_dir
        ).prepare_build_context_to_temp_dir()


def test_prepare_build_context_does_not_log_when_disabled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.docker.images.create.utils.build_context_creator.build_config",
        lambda: SimpleNamespace(log_build_context_content=False),
    )
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM scratch\n")
    source_file = tmp_path / "data.txt"
    source_file.write_text("payload")
    image_info = _create_image_info(dockerfile, {"data.txt": str(source_file)})
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    BuildContextCreator(
        str(build_dir), image_info, log_dir
    ).prepare_build_context_to_temp_dir()

    assert not (log_dir / "docker-build-context.log").exists()
    assert not (log_dir / "Dockerfile.generated").exists()


def test_prepare_build_context_logs_when_enabled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    monkeypatch.setattr(
        "exasol_integration_test_docker_environment.lib.docker.images.create.utils.build_context_creator.build_config",
        lambda: SimpleNamespace(log_build_context_content=True),
    )
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM scratch\nCOPY data.txt /data.txt\n")
    source_file = tmp_path / "data.txt"
    source_file.write_text("payload")
    image_info = _create_image_info(dockerfile, {"data.txt": str(source_file)})
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    BuildContextCreator(
        str(build_dir), image_info, log_dir
    ).prepare_build_context_to_temp_dir()

    context_log = log_dir / "docker-build-context.log"
    generated_dockerfile_log = log_dir / "Dockerfile.generated"
    assert context_log.exists()
    assert generated_dockerfile_log.exists()
    assert str(build_dir / "data.txt") in context_log.read_text()
    assert "COPY data.txt /data.txt" in generated_dockerfile_log.read_text()
