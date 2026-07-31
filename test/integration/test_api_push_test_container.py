from test.integration.get_test_container_content import (
    get_test_container_content,
)

from exasol_integration_test_docker_environment.lib import api
from exasol_integration_test_docker_environment.testing import luigi_utils
from exasol_integration_test_docker_environment.testing.docker_registry import (
    LocalDockerRegistryContextManager,
)


def test_docker_push(api_isolation):
    with LocalDockerRegistryContextManager(api_isolation.name) as docker_registry:
        docker_repository_name = docker_registry.name
        try:
            image_info = api.push_test_container(
                source_docker_repository_name=docker_repository_name,
                target_docker_repository_name=docker_repository_name,
                test_container_content=get_test_container_content(),
                output_directory=api_isolation.output_dir,
                build_name="integration",
            )
            images = docker_registry.images
            assert (
                len(images["tags"]) == 2
            ), f"{images} doesn't have the expected 2 tags, it has {len(images['tags'])}"
            expected_tags = {
                image_info.get_target_complete_tag(),
                image_info.get_target_build_name_complete_tag(),
            }
            assert set(images["tags"]) == expected_tags

        finally:
            luigi_utils.clean(docker_repository_name)
