import docker
import pytest

from exasol_integration_test_docker_environment.lib import api
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.docker.images.image_info import (
    ImageState,
)
from exasol_integration_test_docker_environment.test.get_test_container_content import (
    MOCK_TEST_CONTAINER_PATH,
    get_test_container_content,
)

TEST_CONTAINER_CONTENT = get_test_container_content(MOCK_TEST_CONTAINER_PATH)


def test_build_test_container(api_isolation):
    docker_repository_name = api_isolation.docker_repository_name
    image_info = api.build_test_container(
        target_docker_repository_name=docker_repository_name,
        test_container_content=TEST_CONTAINER_CONTENT,
        output_directory=api_isolation.output_dir,
    )
    with ContextDockerClient() as docker_client:
        try:
            image = docker_client.images.get(image_info.get_target_complete_name())
        except docker.errors.ImageNotFound as e:
            available_images = [" ".join(img.tags) for img in docker_client.images.list()]
            available_images_str = "\n".join(available_images)
            pytest.fail(f"Failed to find image '{image_info.get_target_complete_name()}'. Available images: \n{available_images_str}")
        assert len(image.tags) == 1
        assert image.tags[0] == image_info.get_target_complete_name()
        assert image_info.image_state == ImageState.WAS_BUILD.name


def test_build_test_container_use_cached(api_isolation):
    docker_repository_name = api_isolation.docker_repository_name
    image_info1 = api.build_test_container(
        target_docker_repository_name=docker_repository_name,
        test_container_content=TEST_CONTAINER_CONTENT,
        output_directory=api_isolation.output_dir,
    )
    assert image_info1.image_state == ImageState.WAS_BUILD.name
    image_info2 = api.build_test_container(
        target_docker_repository_name=docker_repository_name,
        test_container_content=TEST_CONTAINER_CONTENT,
        output_directory=api_isolation.output_dir,
    )
    assert image_info2.image_state == ImageState.USED_LOCAL.name


def test_build_test_container_force_rebuild(api_isolation):
    docker_repository_name = api_isolation.docker_repository_name
    image_info1 = api.build_test_container(
        target_docker_repository_name=docker_repository_name,
        test_container_content=TEST_CONTAINER_CONTENT,
        output_directory=api_isolation.output_dir,
    )
    assert image_info1.image_state == ImageState.WAS_BUILD.name
    image_info2 = api.build_test_container(
        target_docker_repository_name=docker_repository_name,
        test_container_content=TEST_CONTAINER_CONTENT,
        force_rebuild=True,
        output_directory=api_isolation.output_dir,
    )
    assert image_info2.image_state == ImageState.WAS_BUILD.name
