from pathlib import Path
from unittest.mock import Mock

import pytest

from exasol_integration_test_docker_environment.lib.docker.images.create.utils.build_context_hasher import (
    BuildContextHasher,
)
from exasol_integration_test_docker_environment.lib.docker.images.image_info import (
    ImageDescription,
)


def _create_image_description(
    dockerfile: Path, data_file: Path, image_changing_build_arguments: dict[str, str]
) -> ImageDescription:
    return ImageDescription(
        dockerfile=str(dockerfile),
        image_changing_build_arguments=image_changing_build_arguments,
        transparent_build_arguments={"X": "ignored"},
        mapping_of_build_files_and_directories={"context/data.txt": str(data_file)},
    )


def _hash_from_description(image_description: ImageDescription) -> str:
    hasher = BuildContextHasher(Mock(), image_description)
    return hasher.generate_image_hash({})


def test_generate_image_hash_fix_value(
    tmp_path: Path,
):
    """
    Validate impact of content of "Dockerfile" on hash sum.
    """

    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM scratch\nCOPY data.txt /data.txt\n")

    build_file = tmp_path / "data.txt"
    build_file.write_text("identical content")

    image_description_one = _create_image_description(
        dockerfile=dockerfile,
        data_file=build_file,
        image_changing_build_arguments={"A": "1", "B": "2"},
    )

    hash_one = _hash_from_description(image_description_one)
    expected_hash = "TZVUSOHGBFQGY4WBB3CDR7Y6IBTMSJ6LYEJLLTWBPMCRTYA46M6A"
    assert hash_one == expected_hash, f"Hash one={hash_one}, hash two={expected_hash}"


@pytest.mark.parametrize(
    "docker_file_content_two, expected_result",
    [
        ("FROM scratch\nCOPY data.txt /data.txt\n", True),
        ("FROM scratch\nCOPY data.txt /data.txt\necho Hello world", False),
    ],
)
def test_generate_image_hash_docker_file_content(
    tmp_path: Path, docker_file_content_two: str, expected_result: bool
):
    """
    Validate impact of content of "Dockerfile" on hash sum.
    """

    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM scratch\nCOPY data.txt /data.txt\n")

    build_file = tmp_path / "data.txt"
    build_file.write_text("identical content")

    image_description_one = _create_image_description(
        dockerfile=dockerfile,
        data_file=build_file,
        image_changing_build_arguments={"A": "1", "B": "2"},
    )
    image_description_two = _create_image_description(
        dockerfile=dockerfile,
        data_file=build_file,
        image_changing_build_arguments={"B": "2", "A": "1"},
    )

    hash_one = _hash_from_description(image_description_one)

    dockerfile.write_text(docker_file_content_two)
    hash_two = _hash_from_description(image_description_two)

    result = hash_one == hash_two
    assert result == expected_result, f"Hash one={hash_one}, hash two={hash_two}"


@pytest.mark.parametrize(
    "build_file_content_two, expected_result",
    [
        ("identical content", True),
        ("different content", False),
    ],
)
def test_generate_image_hash_build_file_content(
    tmp_path: Path, build_file_content_two: str, expected_result: bool
):
    """
    Validate impact of argument "image_changing_build_arguments" on hash sum.
    """

    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM scratch\nCOPY data.txt /data.txt\n")

    build_file = tmp_path / "data.txt"
    build_file.write_text("identical content")

    image_description_one = _create_image_description(
        dockerfile=dockerfile,
        data_file=build_file,
        image_changing_build_arguments={"A": "1", "B": "2"},
    )
    image_description_two = _create_image_description(
        dockerfile=dockerfile,
        data_file=build_file,
        image_changing_build_arguments={"B": "2", "A": "1"},
    )

    hash_one = _hash_from_description(image_description_one)

    build_file.write_text(build_file_content_two)
    hash_two = _hash_from_description(image_description_two)

    result = hash_one == hash_two
    assert result == expected_result, f"Hash one={hash_one}, hash two={hash_two}"


@pytest.mark.parametrize(
    "build_arguments, expected_result",
    [
        ({"A": "1", "B": "2"}, True),
        ({"A": "2", "B": "3"}, False),
    ],
)
def test_generate_image_hash_build_arguments(
    tmp_path: Path, build_arguments: dict[str, str], expected_result: bool
):
    """
    Validate impact of build arguments on hash sum.
    """

    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM scratch\nCOPY data.txt /data.txt\n")

    build_file = tmp_path / "data.txt"
    build_file.write_text("identical content")

    image_description_one = _create_image_description(
        dockerfile=dockerfile,
        data_file=build_file,
        image_changing_build_arguments={"A": "1", "B": "2"},
    )
    image_description_two = _create_image_description(
        dockerfile=dockerfile,
        data_file=build_file,
        image_changing_build_arguments=build_arguments,
    )

    hash_one = _hash_from_description(image_description_one)
    hash_two = _hash_from_description(image_description_two)

    result = hash_one == hash_two
    assert result == expected_result, f"Hash one={hash_one}, hash two={hash_two}"


def test_generate_image_hash_transparent_build_arguments(tmp_path: Path):
    """
    Validate that different arguments of transparent_build_arguments have no impact on hash sum.
    """

    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM scratch\nCOPY data.txt /data.txt\n")

    build_file = tmp_path / "data.txt"
    build_file.write_text("identical content")

    build_arguments = {"A": "1", "B": "2"}

    image_description_one = ImageDescription(
        dockerfile=str(dockerfile),
        image_changing_build_arguments=build_arguments,
        transparent_build_arguments={"X": "something"},
        mapping_of_build_files_and_directories={"context/data.txt": str(build_file)},
    )

    image_description_two = ImageDescription(
        dockerfile=str(dockerfile),
        image_changing_build_arguments=build_arguments,
        transparent_build_arguments={"Y": "something different"},
        mapping_of_build_files_and_directories={"context/data.txt": str(build_file)},
    )

    hash_one = _hash_from_description(image_description_one)
    hash_two = _hash_from_description(image_description_two)

    assert hash_one == hash_two, f"Hash one={hash_one}, hash two={hash_two}"
