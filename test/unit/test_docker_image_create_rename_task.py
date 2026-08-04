from unittest.mock import (
    MagicMock,
    call,
)

from exasol_integration_test_docker_environment.lib.docker.images.create.docker_image_create_task import (
    DockerCreateImageTask,
)
from exasol_integration_test_docker_environment.lib.docker.images.image_info import (
    ImageInfo,
)


def test_retag_source_image_includes_build_name_tag():
    image_info = ImageInfo(
        source_repository_name="source",
        target_repository_name="target",
        source_tag="flavor-goal",
        target_tag="flavor-goal",
        hash_value="HASH",
        commit="commit",
        image_description=None,
        build_name="BUILD",
    )
    task = MagicMock(spec=DockerCreateImageTask)
    docker_client = task._get_docker_client.return_value.__enter__.return_value
    image = docker_client.images.get.return_value

    DockerCreateImageTask.rename_source_image_to_target_image(task, image_info)

    docker_client.images.get.assert_called_once_with("source:flavor-goal_HASH")
    assert image.tag.call_args_list == [
        call(repository="target", tag="flavor-goal_HASH"),
        call(repository="target", tag="flavor-goal_BUILD"),
    ]
