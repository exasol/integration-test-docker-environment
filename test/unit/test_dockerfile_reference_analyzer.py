from datetime import datetime
from pathlib import Path

from exasol_integration_test_docker_environment.lib.docker.images.create.utils.dockerfile_reference_analyzer import (
    find_external_image_references,
    find_missing_external_image_references,
)
from exasol_integration_test_docker_environment.lib.docker.images.image_info import (
    ImageDescription,
    ImageInfo,
    ImageState,
    Platform,
)


def _create_image_info(
    dockerfile: Path, depends_on_images: dict[str, ImageInfo] | None = None
) -> ImageInfo:
    image_description = ImageDescription(
        dockerfile=str(dockerfile),
        image_changing_build_arguments={},
        transparent_build_arguments={},
        mapping_of_build_files_and_directories={},
        additional_resources={},
    )
    return ImageInfo(
        source_repository_name="source/repo",
        target_repository_name="target/repo",
        source_tag="source-tag",
        target_tag="target-tag",
        hash_value="HASH",
        commit="commit",
        image_description=image_description,
        build_name="build",
        build_date_time=datetime.utcnow(),
        image_state=ImageState.NEEDS_TO_BE_BUILD,
        depends_on_images=depends_on_images or {},
        platform=Platform.X64,
    )


def _create_dependency_image_info(name: str) -> ImageInfo:
    return ImageInfo(
        source_repository_name=name,
        target_repository_name=name,
        source_tag="source",
        target_tag="target",
        hash_value="HASH",
        commit="commit",
        image_description=None,
        build_name="build",
        build_date_time=datetime.utcnow(),
        image_state=ImageState.WAS_BUILD,
        depends_on_images={},
        platform=Platform.X64,
    )


def test_find_external_image_references(tmp_path: Path):
    dockerfile = tmp_path / "Dockerfile"
    dependency_image = _create_dependency_image_info("dependency/repo")
    dependency_reference = dependency_image.get_target_complete_name()
    dockerfile.write_text(
        "\n".join(
            [
                f"FROM {dependency_reference} AS local_base",
                "FROM external/from:1 AS external_from",
                "FROM local_base",
                "COPY --from=external_from /a /a",
                f"COPY --from={dependency_reference} /b /b",
                "COPY --from=external/copy:2 /c /c",
                "COPY --from=0 /d /d",
            ]
        )
    )
    image_info = _create_image_info(
        dockerfile, depends_on_images={"build_step": dependency_image}
    )

    references = find_external_image_references(dockerfile.read_text(), image_info)

    assert references == ["external/from:1", "external/copy:2"]


def test_find_missing_external_image_references(tmp_path: Path):
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text(
        "\n".join(
            [
                "FROM external/from:1 AS external_from",
                "FROM scratch",
                "COPY --from=external_from /a /a",
                "COPY --from=external/copy:2 /b /b",
            ]
        )
    )
    image_info = _create_image_info(dockerfile)

    missing = find_missing_external_image_references(
        image_info, lambda reference: reference == "external/from:1"
    )

    assert missing == ["external/copy:2"]
