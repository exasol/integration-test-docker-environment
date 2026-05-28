from exasol_integration_test_docker_environment.lib.docker.images.image_info import (
    ImageDescription,
    ImageInfo,
    Platform,
)


def _create_image_info(build_name: str = "") -> ImageInfo:
    return ImageInfo(
        source_repository_name="repo",
        target_repository_name="repo",
        source_tag="flavor-goal",
        target_tag="flavor-goal",
        hash_value="HASH",
        commit="commit",
        image_description=ImageDescription(
            dockerfile="Dockerfile",
            image_changing_build_arguments={},
            transparent_build_arguments={},
            mapping_of_build_files_and_directories={},
            additional_resources={},
        ),
        build_name=build_name,
        platform=Platform.X64,
    )


def test_source_tag_keeps_hash():
    image_info = _create_image_info(build_name="BUILD")

    assert image_info.get_source_complete_tag() == "flavor-goal_x64_HASH"
    assert image_info.get_source_complete_name() == "repo:flavor-goal_x64_HASH"


def test_target_tag_uses_build_name_when_set():
    image_info = _create_image_info(build_name="BUILD")

    assert image_info.get_target_complete_tag() == "flavor-goal_x64_BUILD"
    assert image_info.get_target_complete_name() == "repo:flavor-goal_x64_BUILD"


def test_target_tag_falls_back_to_hash_when_build_name_missing():
    image_info = _create_image_info()

    assert image_info.get_target_complete_tag() == "flavor-goal_x64_HASH"
