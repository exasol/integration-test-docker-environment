from typing import Any

import pytest

from exasol_integration_test_docker_environment.lib.docker.images.image_info import (
    ImageDescription,
    ImageInfo,
    ImageState,
    Platform,
)


def _create_image_info(
    build_name: str = "",
    platform: Any = Platform.X64,
    image_state: Any = ImageState.NOT_EXISTING,
    source_tag: str = "flavor-goal",
    target_tag: str = "flavor-goal",
    hash_value: str = "HASH",
) -> ImageInfo:
    return ImageInfo(
        source_repository_name="repo",
        target_repository_name="repo",
        source_tag=source_tag,
        target_tag=target_tag,
        hash_value=hash_value,
        commit="commit",
        image_description=ImageDescription(
            dockerfile="Dockerfile",
            image_changing_build_arguments={},
            transparent_build_arguments={},
            mapping_of_build_files_and_directories={},
            additional_resources={},
        ),
        build_name=build_name,
        image_state=image_state,
        platform=platform,
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


def test_constructor_accepts_string_enums():
    image_info = _create_image_info(
        image_state="WAS_BUILD",
        platform="ARM_64",
    )

    assert image_info.image_state == ImageState.WAS_BUILD.name
    assert image_info.platform == Platform.ARM_64.value


def test_constructor_accepts_enum_values():
    image_info = _create_image_info(
        image_state=ImageState.USED_LOCAL,
        platform=Platform.ARM_64,
    )

    assert image_info.image_state == ImageState.USED_LOCAL.name
    assert image_info.platform == Platform.ARM_64.value


def test_constructor_allows_none_for_optional_state_and_platform():
    image_info = _create_image_info(image_state=None, platform=None)

    assert image_info.image_state is None
    assert image_info.platform is None


def test_constructor_rejects_invalid_image_state():
    with pytest.raises(TypeError, match="image_state not supported"):
        _create_image_info(image_state=object())


def test_constructor_rejects_invalid_platform():
    with pytest.raises(TypeError, match="platform not supported"):
        _create_image_info(platform=object())


def test_constructor_rejects_unknown_image_state_name():
    with pytest.raises(KeyError):
        _create_image_info(image_state="UNKNOWN")


def test_constructor_rejects_unknown_platform_name():
    with pytest.raises(KeyError):
        _create_image_info(platform="UNKNOWN")


def test_target_tag_without_platform_uses_only_tag_and_suffix():
    image_info = _create_image_info(platform=None)

    assert image_info.get_target_complete_tag() == "flavor-goal_HASH"


def test_target_tag_is_truncated_to_docker_limit():
    long_tag = "x" * 120
    image_info = _create_image_info(
        source_tag=long_tag,
        target_tag=long_tag,
        hash_value="HASH",
    )

    assert len(image_info.get_source_complete_tag()) == 128
    assert len(image_info.get_target_complete_tag()) == 128
    assert image_info.get_target_complete_tag() == f"{long_tag}_x64_HAS"


def test_constructor_rejects_tags_that_exceed_maximum_complete_length():
    long_tag = "x" * 150

    with pytest.raises(Exception, match="Complete Tag to long"):
        _create_image_info(source_tag=long_tag, target_tag=long_tag)
