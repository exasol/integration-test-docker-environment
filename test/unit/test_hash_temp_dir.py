import base64
import contextlib
import os
from collections.abc import Iterator
from pathlib import (
    Path,
    PurePath,
)

import pytest

from exasol_integration_test_docker_environment.lib.docker.images.create.utils.file_directory_list_hasher import (
    FileDirectoryListHasher,
    PathMapping,
)


def simple_path_mapping(src: Path) -> PathMapping:
    return PathMapping(destination=PurePath(src.name), source=src)


@contextlib.contextmanager
def change_directory(directory: Path):
    old_dir = os.getcwd()
    os.chdir(directory)
    yield
    os.chdir(old_dir)


@pytest.fixture(scope="module")
def temp_dirs(tmp_path_factory: pytest.TempPathFactory) -> Iterator[dict[str, Path]]:
    hash_temp_path = tmp_path_factory.mktemp("HashTempDirTest")
    test_dir1 = hash_temp_path / "test1"
    test_dir2 = hash_temp_path / "test2"
    test_dir3 = hash_temp_path / "test3"

    def generate_test_dir(test_dir: Path):
        level1 = 5
        level2 = 5
        level3 = 5
        level4 = 5
        level5 = 5
        for i1 in range(level1):
            for i2 in range(level2):
                for i3 in range(level3):
                    for i4 in range(level4):
                        path = (
                            test_dir
                            / "level0"
                            / f"level1_{i1}"
                            / f"level2_{i2}"
                            / f"level3_{i3}"
                            / f"level4_{i4}"
                        )
                        path.mkdir(parents=True, exist_ok=False)
                        test_path = path / "test"
                        test_path.mkdir(parents=True, exist_ok=False)
                        for i5 in range(level5):
                            file = path / f"level5_file_{i5}"
                            file_content = (
                                "/"
                                + str(path.relative_to(test_dir))
                                + "//"
                                + f"level5_file_{i5}"
                            )
                            file.write_text(file_content)

    # Setup
    generate_test_dir(test_dir1)
    generate_test_dir(test_dir2)

    test_dir3_subdir = test_dir3 / "d"
    test_dir3_subdir.mkdir(parents=True, exist_ok=False)
    test_dir3_test_file = test_dir3 / "f"
    test_dir3_test_file.write_text("test")

    test_file = (
        hash_temp_path / "SEFQWEFWQEHDUWEFDGZWGDZWEFDUWESGRFUDWEGFUDWAFGWAZESGFDWZA"
    )
    test_file.write_text("test")

    yield {
        "temp_dir": hash_temp_path,
        "test_dir1": test_dir1,
        "test_dir2": test_dir2,
        "test_dir3": test_dir3,
        "test_file": test_file,
    }


def test_single_character_directory_name(temp_dirs):
    hasher = FileDirectoryListHasher(
        hashfunc="sha256", hash_directory_names=True, hash_file_names=True
    )
    with change_directory(temp_dirs["test_dir3"]):
        hash_val = hasher.hash([simple_path_mapping(Path("."))])
        ascii_hash = base64.b32encode(hash_val).decode("ASCII")
        assert ascii_hash == "LVE2ZFQRMP6QLY43MKMZRHIEHE7KNSUS5LFWVJKPOWMI6JUPZHEQ===="


@pytest.mark.parametrize(
    "hash_directory_names, hash_file_names, expected",
    [
        (False, False, "SVGVUSP5ODM3RPG3GXJFEJTYFGKX67XX7JWHJ6EEDG64L2BCBH2A===="),
        (True, True, "7D34CBUU2SNSWF3UFM6A7BYFJVV5ZFEY5F6THIMGJY725WC45KEA===="),
    ],
    ids=["only_fixed_hash", "with_path"],
)
def test_file_content(hash_directory_names, hash_file_names, expected, temp_dirs):
    hasher = FileDirectoryListHasher(
        hashfunc="sha256",
        hash_directory_names=hash_directory_names,
        hash_file_names=hash_file_names,
    )
    hash_val = hasher.hash([simple_path_mapping(temp_dirs["test_file"])])
    ascii_hash = base64.b32encode(hash_val).decode("ASCII")
    assert ascii_hash == expected


@pytest.mark.parametrize(
    "hash_directory_names, hash_file_names, expected",
    [
        (False, False, "TM2V22T326TCTLQ537BZAOR3I5NVHXE6IDJ4TXPCJPTUGDTI5WYQ===="),
        (True, True, "EZ3ER6KZHAAYG4JNFGFLHUI7TVHZVIRVOV4QWJT4ERQ4XGI2GLUA===="),
    ],
    ids=["only_fixed_hash", "relative_paths_fixed_hash"],
)
def test_directory(hash_directory_names, hash_file_names, expected, temp_dirs):
    hasher = FileDirectoryListHasher(
        hashfunc="sha256",
        hash_directory_names=hash_directory_names,
        hash_file_names=hash_file_names,
    )
    hash_val = hasher.hash([simple_path_mapping(temp_dirs["test_dir1"])])
    ascii_hash = base64.b32encode(hash_val).decode("ASCII")
    assert ascii_hash == expected


def test_directory_to_same_destination_equal(temp_dirs):
    hasher = FileDirectoryListHasher(
        hashfunc="sha256", hash_directory_names=True, hash_file_names=True
    )
    hash1 = hasher.hash([PathMapping(PurePath("test"), Path(temp_dirs["test_dir1"]))])
    hash2 = hasher.hash([PathMapping(PurePath("test"), Path(temp_dirs["test_dir2"]))])
    ascii_hash1 = base64.b32encode(hash1).decode("ASCII")
    ascii_hash2 = base64.b32encode(hash2).decode("ASCII")
    assert ascii_hash1 == ascii_hash2


@pytest.mark.parametrize(
    "hash_directory_names_dir1, hash_file_names_dir1, hash_directory_names_dir2, hash_file_names_dir2, expected",
    [
        (False, False, False, False, True),
        (True, True, True, True, False),
        (False, False, True, True, False),
        (False, False, False, True, False),
        (False, False, True, False, False),
        (False, True, True, False, False),
    ],
)
def test_two_directories(
    hash_directory_names_dir1,
    hash_file_names_dir1,
    hash_directory_names_dir2,
    hash_file_names_dir2,
    expected,
    temp_dirs,
):
    hasher_content_only = FileDirectoryListHasher(
        hashfunc="sha256",
        hash_directory_names=hash_directory_names_dir1,
        hash_file_names=hash_file_names_dir1,
    )
    hasher_with_paths = FileDirectoryListHasher(
        hashfunc="sha256",
        hash_directory_names=hash_directory_names_dir2,
        hash_file_names=hash_file_names_dir2,
    )
    hash1_content_only = hasher_content_only.hash(
        [simple_path_mapping(temp_dirs["test_dir1"])]
    )
    hash2_with_paths = hasher_with_paths.hash(
        [simple_path_mapping(temp_dirs["test_dir2"])]
    )
    ascii_hash1 = base64.b32encode(hash1_content_only).decode("ASCII")
    ascii_hash2 = base64.b32encode(hash2_with_paths).decode("ASCII")
    result = ascii_hash1 == ascii_hash2
    assert (
        result == expected
    ), f"ascii_hash1='{ascii_hash1}' ascii_hash2='{ascii_hash2}' result={result}"
