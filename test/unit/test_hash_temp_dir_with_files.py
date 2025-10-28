import base64
import os
from pathlib import Path, PurePath

import pytest

from exasol_integration_test_docker_environment.lib.docker.images.create.utils.file_directory_list_hasher import (
    FileDirectoryListHasher,
    PathMapping,
)

@pytest.fixture
def temp_dirs(tmp_path):
    test_path1 = tmp_path / "test1"
    test_path1.mkdir()
    test_path2 = tmp_path / "test2"
    test_path2.mkdir()
    yield test_path1, test_path2



def test_file_name_with_relative_path(temp_dirs):
    """
    Test that hashing of same files in different paths gives same result.
    1. Mapping dest="test.txt", src="/tmp/.../$tmpA/test.txt"
    2. Mapping dest="test.txt", src="/tmp/.../$tmpB/test.txt"
    """
    test_path1, test_path2 = temp_dirs
    hasher = FileDirectoryListHasher(
        followlinks=True,
        hashfunc="sha256",
        hash_file_names=True,
        hash_directory_names=True,
        hash_permissions=True,
    )

    test_file1 = test_path1 / "test.txt"
    test_file1.write_text("test")
    mapping1 = PathMapping(PurePath("test.txt"), test_file1)
    hash1 = hasher.hash([mapping1])

    test_file2 = test_path2 / "test.txt"
    test_file2.write_text("test")
    mapping2 = PathMapping(PurePath("test.txt"), test_file2)
    hash2 = hasher.hash([mapping2])

    ascii_hash1 = base64.b32encode(hash1).decode("ASCII")
    ascii_hash2 = base64.b32encode(hash2).decode("ASCII")
    assert ascii_hash1 == ascii_hash2



def test_file_name_with_relative_path_in_same_sub_path(temp_dirs):
    """
    Test that hashing of same files in different paths, but under same subpath, gives same result
    1. Mapping dest="level0/test.txt", src="/tmp/.../$tmpA/level0/test.txt"
    2. Mapping dest="level0/test.txt", src="/tmp/.../$tmpB/level0/test.txt"
    """
    test_path1, test_path2 = temp_dirs
    hasher = FileDirectoryListHasher(
        followlinks=True,
        hashfunc="sha256",
        hash_file_names=True,
        hash_directory_names=True,
        hash_permissions=True,
    )
    p1 = test_path1 / "level0"
    p1.mkdir()
    test_file1 = p1 / "test.txt"
    test_file1.write_text("test")
    mapping1 = PathMapping(PurePath("level0/test.txt"), test_file1)
    hash1 = hasher.hash([mapping1])

    p2 = test_path2 / "level0"
    p2.mkdir()
    test_file2 = p2 / "test.txt"
    test_file2.write_text("test")
    mapping2 = PathMapping(PurePath("level0/test.txt"), test_file2)
    hash2 = hasher.hash([mapping2])

    ascii_hash1 = base64.b32encode(hash1).decode("ASCII")
    ascii_hash2 = base64.b32encode(hash2).decode("ASCII")
    assert ascii_hash1 == ascii_hash2



def test_file_name_with_relative_path_in_different_sub_path(temp_dirs):
    """
    Test that hashing of same files in different paths, and different subpaths, gives different result.
    1. Mapping dest="level0/test.txt", src="/tmp/.../level0/test.txt"
    2. Mapping dest="level0/level1_0/test.txt", src="/tmp/.../level0/level1_0/test.txt"
    """

    test_path1, test_path2 = temp_dirs
    hasher = FileDirectoryListHasher(
        followlinks=True,
        hashfunc="sha256",
        hash_file_names=True,
        hash_directory_names=True,
        hash_permissions=True,
    )
    p1 = test_path1 / "level0"
    p1.mkdir()
    test_file1 = p1 / "test.txt"
    test_file1.write_text("test")
    hash1 = hasher.hash(
        [PathMapping(PurePath("level0/test.txt"), test_file1)]
    )

    p2 = test_path2 / "level0" / "level1_0"
    p2.mkdir(parents=True)
    test_file2 = p2 / "test.txt"
    test_file2.write_text("test")
    hash2 = hasher.hash(
        [PathMapping(PurePath("level0/level1_0/test.txt"), test_file2)]
    )

    ascii_hash1 = base64.b32encode(hash1).decode("ASCII")
    ascii_hash2 = base64.b32encode(hash2).decode("ASCII")
    assert ascii_hash1 != ascii_hash2



def test_file_name_with_relative_path_in_relative_path_as_argument(temp_dirs):
    """
    Test that hashing of same files in different paths, gives same result, using relative paths as argument
    for source and destination path in the mapping.
    For that, we need to change pwd before running hasher_content_only.hash.
    1. Mapping dest="test.txt", src="test.txt"
    2. Mapping dest="test.txt", src="test.txt"
    """
    test_path1, test_path2 = temp_dirs
    hasher = FileDirectoryListHasher(
        followlinks=True,
        hashfunc="sha256",
        hash_file_names=True,
        hash_directory_names=True,
        hash_permissions=True,
    )
    test_file = "test.txt"
    old_pwd = os.getcwd()
    try:
        os.chdir(test_path1)
        Path(test_file).write_text("test")
        mapping1 = PathMapping(PurePath("test.txt"), Path(test_file))
        hash1 = hasher.hash([mapping1])

        os.chdir(test_path2)
        Path(test_file).write_text("test")
        mapping2 = PathMapping(PurePath("test.txt"), Path(test_file))
        hash2 = hasher.hash([mapping2])

        ascii_hash1 = base64.b32encode(hash1).decode("ASCII")
        ascii_hash2 = base64.b32encode(hash2).decode("ASCII")
        assert ascii_hash1 == ascii_hash2
    finally:
        os.chdir(old_pwd)



def test_duplicated_file_mapping_raises_exception(temp_dirs):
    """
    Test that a duplicated mapping raises an exception.
    1. Mapping dest="test.txt", src="/tmp/.../$tmpB/level0/level1_0/test.txt"
    2. Mapping dest="test.txt", src="/tmp/.../$tmpB/level0/level1_1/test.txt"
    """
    test_path1, test_path2 = temp_dirs
    hasher = FileDirectoryListHasher(
        followlinks=True,
        hashfunc="sha256",
        hash_file_names=True,
        hash_directory_names=True,
        hash_permissions=True,
    )
    p1 = test_path1 / "level0" / "level1_0"
    p1.mkdir(parents=True)
    test_file1 = p1 / "test.txt"
    test_file1.write_text("test")

    p2 = test_path2 / "level0" / "level1_1"
    p2.mkdir(parents=True)
    test_file2 = p2 / "test.txt"
    test_file2.write_text("test")

    path_mappings = [
        PathMapping(PurePath("test.txt"), test_file1),
        PathMapping(PurePath("test.txt"), test_file2),
    ]
    with pytest.raises(AssertionError):
        hasher.hash(path_mappings)



def test_duplicated_path_mapping_raises_exception(temp_dirs):
    """
    Test that a duplicated mapping raises an exception. Mapping source is here a directory containing one file.
    1. Mapping dest="test", src="/tmp/.../$tmpA/level0/level1_0", content under src="test/test.txt"
    2. Mapping dest="test", src="/tmp/.../$tmpB/level0/level1_1", content under src="test/test.txt"
    """
    test_path1, test_path2 = temp_dirs
    hasher = FileDirectoryListHasher(
        followlinks=True,
        hashfunc="sha256",
        hash_file_names=True,
        hash_directory_names=True,
        hash_permissions=True,
    )

    p1 = test_path1 / "level0" / "level1_0" / "test"
    test_file1 = p1 / "test.txt"
    p1.mkdir(parents=True)
    test_file1.write_text("test")

    p2 = test_path2 / "level0" / "level1_1" / "test"
    p2.mkdir(parents=True)
    test_file2 = p2 / "test.txt"
    test_file2.write_text("test")

    path1 = p1.parent
    path2 = p2.parent
    path_mappings = [
        PathMapping(PurePath("test"), path1),
        PathMapping(PurePath("test"), path2),
    ]
    with pytest.raises(AssertionError):
        hasher.hash(path_mappings)



def test_duplicated_path_mapping_with_subpath_raises_exception(temp_dirs):
    """
    Test that a duplicated mapping raises an exception. Mapping source is here a directory containing one file.
    1. Mapping dest="test/abc", src="/tmp/.../$tmpA/level0/level1_0", content under src="test/test.txt"
    2. Mapping dest="test/abc", src="/tmp/.../$tmpB/level0/level1_1", content under src="test/test.txt"
    """
    test_path1, test_path2 = temp_dirs
    hasher = FileDirectoryListHasher(
        followlinks=True,
        hashfunc="sha256",
        hash_file_names=True,
        hash_directory_names=True,
        hash_permissions=True,
    )

    p1 = test_path1 / "level0" / "level1_0" / "test"
    test_file1 = p1 / "test.txt"
    p1.mkdir(parents=True)
    test_file1.write_text("test")
    p2 = test_path2 / "level0" / "level1_1" / "test"
    p2.mkdir(parents=True)
    test_file2 = p2 / "test.txt"
    test_file2.write_text("test")

    path1 = p1.parent
    path2 = p2.parent
    destination_path = PurePath("test/abc")
    path_mappings = [
        PathMapping(destination_path, path1),
        PathMapping(destination_path, path2),
    ]
    with pytest.raises(AssertionError):
        hasher.hash(path_mappings)


def test_duplicated_path_mapping_with_destination_subpath_raises_exception(temp_dirs):
    """
    Test that a duplicated mapping raises an exception.
    In this scenario we have one path which maps to a destination containing a subpath;
    the second path maps to root destination of the first, but contains the subdirectory of the first in the
    source directory.
    1. Mapping dest="test", src="/tmp/.../$tmpA", content under src="abc/level0/level1_0/test/test.txt"
    2. Mapping dest="test/abc", src="/tmp/.../$tmpB", content under src="level0/level1_0/test/test.txt"
    """
    test_path1, test_path2 = temp_dirs
    hasher = FileDirectoryListHasher(
        followlinks=True,
        hashfunc="sha256",
        hash_file_names=True,
        hash_directory_names=True,
        hash_permissions=True,
    )
    p1 = test_path1 / "level1_0" / "test"
    test_file1 = p1 / "test.txt"
    p1.mkdir(parents=True)
    test_file1.write_text("test")
    p2 = test_path2 / "abc" / "level1_0" / "test"
    p2.mkdir(parents=True)
    test_file2 = p2 / "test.txt"
    test_file2.write_text("test")

    path1 = test_path1
    path2 = test_path2

    path_mappings = [
        PathMapping(PurePath("test/abc"), path1),
        PathMapping(PurePath("test"), path2),
    ]
    with pytest.raises(AssertionError):
        hasher.hash(path_mappings)
