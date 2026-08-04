import shutil
from pathlib import Path

import docker
import luigi

from exasol_integration_test_docker_environment.lib.base.run_task import (
    generate_root_task,
)
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.docker.images.create.docker_image_create_task import (
    DockerCreateImageTask,
)
from exasol_integration_test_docker_environment.lib.docker.images.image_info import (
    ImageInfo,
    ImageState,
    Platform,
)

SOURCE_REPOSITORY = "itde-test-source-image-retag"
TARGET_REPOSITORY = "itde-test-target-image-retag"


def _remove_image_tag(image_reference: str) -> None:
    with ContextDockerClient() as docker_client:
        try:
            docker_client.images.remove(image_reference, force=True)
        except docker.errors.ImageNotFound:
            pass


def test_retag_local_source_image_includes_build_name(
    luigi_output: Path, running_platform: Platform
):
    image_info = ImageInfo(
        source_repository_name=SOURCE_REPOSITORY,
        target_repository_name=TARGET_REPOSITORY,
        source_tag="stage",
        target_tag="stage",
        hash_value="HASH",
        commit="commit",
        image_description=None,
        build_name="integration",
        image_state=ImageState.SOURCE_LOCALLY_AVAILABLE,
        platform=running_platform,
    )
    source_reference = image_info.get_source_complete_name()
    target_hash_reference = image_info.get_target_complete_name()
    target_build_name_reference = (
        f"{TARGET_REPOSITORY}:{image_info.get_target_build_name_complete_tag()}"
    )
    build_context = luigi_output / "source-image"
    build_context.mkdir()
    (build_context / "marker").write_text("source image")
    (build_context / "Dockerfile").write_text("FROM scratch\nCOPY marker /marker\n")

    with ContextDockerClient() as docker_client:
        docker_client.images.build(
            path=str(build_context), tag=source_reference, rm=True
        )

    task = generate_root_task(
        task_class=DockerCreateImageTask,
        image_name=f"{TARGET_REPOSITORY}:stage",
        image_info=image_info,
    )
    try:
        assert luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
        assert task.get_result().image_state == ImageState.WAS_TAGED.name
        with ContextDockerClient() as docker_client:
            target_image = docker_client.images.get(target_hash_reference)
            assert target_hash_reference in target_image.tags
            assert target_build_name_reference in target_image.tags
    finally:
        _remove_image_tag(target_build_name_reference)
        _remove_image_tag(target_hash_reference)
        _remove_image_tag(source_reference)
        if task._get_tmp_path_for_job().exists():
            shutil.rmtree(task._get_tmp_path_for_job())
