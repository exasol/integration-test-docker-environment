import base64
import os
import tempfile
import unittest
from pathlib import (
    Path,
    PurePath,
)

from exasol_integration_test_docker_environment.lib.docker.images.create.utils.file_directory_list_hasher import (
    FileDirectoryListHasher,
    PathMapping,
)


class HashTempDirTest(unittest.TestCase):
    """
    Deprecated. Replaced by "./test/unit/test_hash_temp_dir_with_files.py
    """

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.test_path1 = self.temp_path / "test1"
        self.test_path1.mkdir()
        self.test_path2 = self.temp_path / "test2"
        self.test_path2.mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_file_name_with_relative_path(self):
        """
        Test that hashing of same files in different paths gives same result.
        1. Mapping dest="test.txt", src="/tmp/.../$tmpA/test.txt"
        2. Mapping dest="test.txt", src="/tmp/.../$tmpB/test.txt"
        """
        hasher_content_only = FileDirectoryListHasher(
            followlinks=True,
            hashfunc="sha256",
            hash_file_names=True,
            hash_directory_names=True,
            hash_permissions=True,
        )
        test_file1 = Path(f"{self.test_path1}/test.txt")
        with open(test_file1, "w") as f:
            f.write("test")
        mapping = PathMapping(PurePath("test.txt"), test_file1)
        hash1_content_only = hasher_content_only.hash([mapping])

        test_file2 = Path(f"{self.test_path2}/test.txt")
        with open(test_file2, "w") as f:
            f.write("test")
        mapping = PathMapping(PurePath("test.txt"), test_file2)
        hash2_content_only = hasher_content_only.hash([mapping])

        ascii_hash1_content_only = base64.b32encode(hash1_content_only).decode("ASCII")
        ascii_hash2_content_only = base64.b32encode(hash2_content_only).decode("ASCII")
        self.assertEqual(ascii_hash1_content_only, ascii_hash2_content_only)

    def test_file_name_with_relative_path_in_same_sub_path(self):
        """
        Test that hashing of same files in different paths, but under same subpath, gives same result
        1. Mapping dest="level0/test.txt", src="/tmp/.../$tmpA/level0/test.txt"
        2. Mapping dest="level0/test.txt", src="/tmp/.../$tmpB/level0/test.txt"
        """
        hasher_content_only = FileDirectoryListHasher(
            followlinks=True,
            hashfunc="sha256",
            hash_file_names=True,
            hash_directory_names=True,
            hash_permissions=True,
        )
        p1 = self.test_path1 / "level0"
        p1.mkdir()
        test_file1 = p1 / "test.txt"
        with open(test_file1, "w") as f:
            f.write("test")
        mapping = PathMapping(PurePath("level0/test.txt"), test_file1)
        hash1_content_only = hasher_content_only.hash([mapping])

        p2 = self.test_path2 / "level0"
        p2.mkdir()
        test_file2 = p2 / "test.txt"
        with open(test_file2, "w") as f:
            f.write("test")
        mapping = PathMapping(PurePath("level0/test.txt"), test_file2)
        hash2_content_only = hasher_content_only.hash([mapping])

        ascii_hash1_content_only = base64.b32encode(hash1_content_only).decode("ASCII")
        ascii_hash2_content_only = base64.b32encode(hash2_content_only).decode("ASCII")
        self.assertEqual(ascii_hash1_content_only, ascii_hash2_content_only)

    def test_file_name_with_relative_path_in_different_sub_path(self):
        """
        Test that hashing of same files in different paths, and different subpaths, gives different result.
        1. Mapping dest="level0/test.txt", src="/tmp/.../level0/test.txt"
        2. Mapping dest="level0/level1_0/test.txt", src="/tmp/.../level0/level1_0/test.txt"
        """
        hasher_content_only = FileDirectoryListHasher(
            followlinks=True,
            hashfunc="sha256",
            hash_file_names=True,
            hash_directory_names=True,
            hash_permissions=True,
        )
        p1 = self.test_path1 / "level0"
        p1.mkdir()
        test_file1 = p1 / "test.txt"
        with open(test_file1, "w") as f:
            f.write("test")
        hash1_content_only = hasher_content_only.hash(
            [PathMapping(PurePath("level0/test.txt"), test_file1)]
        )

        p2 = self.test_path2 / "level0" / "level1_0"
        p2.mkdir(parents=True)
        test_file2 = p2 / "test.txt"

        with open(test_file2, "w") as f:
            f.write("test")
        hash2_content_only = hasher_content_only.hash(
            [PathMapping(PurePath("level0/level1_0/test.txt"), test_file2)]
        )

        ascii_hash1_content_only = base64.b32encode(hash1_content_only).decode("ASCII")
        ascii_hash2_content_only = base64.b32encode(hash2_content_only).decode("ASCII")
        self.assertNotEqual(ascii_hash1_content_only, ascii_hash2_content_only)

    def test_file_name_with_relative_path_in_relative_path_as_argument(self):
        """
        Test that hashing of same files in different paths, gives same result, using relative paths as argument
        for source and destination path in the mapping.
        For that, we need to change pwd before running hasher_content_only.hash.
        1. Mapping dest="test.txt", src="test.txt"
        2. Mapping dest="test.txt", src="test.txt"
        """
        hasher_content_only = FileDirectoryListHasher(
            followlinks=True,
            hashfunc="sha256",
            hash_file_names=True,
            hash_directory_names=True,
            hash_permissions=True,
        )
        test_file = f"test.txt"
        old_pwd = os.getcwd()
        os.chdir(self.test_path1)
        with open(test_file, "w") as f:
            f.write("test")
        mapping = PathMapping(PurePath("test.txt"), Path(test_file))
        hash1_content_only = hasher_content_only.hash([mapping])
        os.chdir(self.test_path2)

        with open(test_file, "w") as f:
            f.write("test")
        mapping = PathMapping(PurePath("test.txt"), Path(test_file))
        hash2_content_only = hasher_content_only.hash([mapping])
        os.chdir(old_pwd)
        ascii_hash1_content_only = base64.b32encode(hash1_content_only).decode("ASCII")
        ascii_hash2_content_only = base64.b32encode(hash2_content_only).decode("ASCII")
        self.assertEqual(ascii_hash1_content_only, ascii_hash2_content_only)

    def test_duplicated_file_mapping_raises_exception(self):
        """
        Test that a duplicated mapping raises an exception.
        1. Mapping dest="test.txt", src="/tmp/.../$tmpB/level0/level1_0/test.txt"
        2. Mapping dest="test.txt", src="/tmp/.../$tmpB/level0/level1_1/test.txt"
        """
        hasher_content_only = FileDirectoryListHasher(
            followlinks=True,
            hashfunc="sha256",
            hash_file_names=True,
            hash_directory_names=True,
            hash_permissions=True,
        )
        p1 = self.test_path1 / "level0" / "level1_0"
        p1.mkdir(parents=True)
        test_file1 = p1 / "test.txt"

        with open(test_file1, "w") as f:
            f.write("test")

        p2 = self.test_path2 / "level0" / "level1_1"
        p2.mkdir(parents=True)
        test_file2 = p2 / "test.txt"
        with open(test_file2, "w") as f:
            f.write("test")

        path_mappings = [
            PathMapping(PurePath("test.txt"), test_file1),
            PathMapping(PurePath("test.txt"), test_file2),
        ]
        self.assertRaises(
            AssertionError, lambda: hasher_content_only.hash(path_mappings)
        )

    def test_duplicated_path_mapping_raises_exception(self):
        """
        Test that a duplicated mapping raises an exception. Mapping source is here a directory containing one file.
        1. Mapping dest="test", src="/tmp/.../$tmpA/level0/level1_0", content under src="test/test.txt"
        2. Mapping dest="test", src="/tmp/.../$tmpB/level0/level1_1", content under src="test/test.txt"
        """
        hasher_content_only = FileDirectoryListHasher(
            followlinks=True,
            hashfunc="sha256",
            hash_file_names=True,
            hash_directory_names=True,
            hash_permissions=True,
        )

        p1 = self.test_path1 / "level0" / "level1_0" / "test"
        test_file1 = p1 / "test.txt"
        p1.mkdir(parents=True)
        with open(test_file1, "w") as f:
            f.write("test")
        p2 = self.test_path2 / "level0" / "level1_1" / "test"
        p2.mkdir(parents=True)
        test_file2 = p2 / "test.txt"
        with open(test_file2, "w") as f:
            f.write("test")

        path1 = p1.parent
        path2 = p2.parent
        path_mappings = [
            PathMapping(PurePath("test"), path1),
            PathMapping(PurePath("test"), path2),
        ]
        self.assertRaises(
            AssertionError, lambda: hasher_content_only.hash(path_mappings)
        )

    def test_duplicated_path_mapping_with_subpath_raises_exception(self):
        """
        Test that a duplicated mapping raises an exception. Mapping source is here a directory containing one file.
        1. Mapping dest="test/abc", src="/tmp/.../$tmpA/level0/level1_0", content under src="test/test.txt"
        2. Mapping dest="test/abc", src="/tmp/.../$tmpB/level0/level1_1", content under src="test/test.txt"
        """
        hasher_content_only = FileDirectoryListHasher(
            followlinks=True,
            hashfunc="sha256",
            hash_file_names=True,
            hash_directory_names=True,
            hash_permissions=True,
        )

        p1 = self.test_path1 / "level0" / "level1_0" / "test"
        test_file1 = p1 / "test.txt"
        p1.mkdir(parents=True)
        with open(test_file1, "w") as f:
            f.write("test")
        p2 = self.test_path2 / "level0" / "level1_1" / "test"
        p2.mkdir(parents=True)
        test_file2 = p2 / "test.txt"
        with open(test_file2, "w") as f:
            f.write("test")

        path1 = p1.parent
        path2 = p2.parent
        destination_path = PurePath("test/abc")
        path_mappings = [
            PathMapping(destination_path, path1),
            PathMapping(destination_path, path2),
        ]
        self.assertRaises(
            AssertionError, lambda: hasher_content_only.hash(path_mappings)
        )

    def test_duplicated_path_mapping_with_destination_subpath_raises_exception(self):
        """
        Test that a duplicated mapping raises an exception.
        In this scenario we have one path which maps to a destination containing a subpath;
        the second path maps to root destination of the first, but contains the subdirectory of the first in the
        source directory.
        1. Mapping dest="test", src="/tmp/.../$tmpA", content under src="abc/level0/level1_0/test/test.txt"
        2. Mapping dest="test/abc", src="/tmp/.../$tmpB", content under src="level0/level1_0/test/test.txt"
        """
        hasher_content_only = FileDirectoryListHasher(
            followlinks=True,
            hashfunc="sha256",
            hash_file_names=True,
            hash_directory_names=True,
            hash_permissions=True,
        )

        p1 = self.test_path1 / "level1_0" / "test"
        test_file1 = p1 / "test.txt"
        p1.mkdir(parents=True)
        with open(test_file1, "w") as f:
            f.write("test")
        p2 = self.test_path2 / "abc" / "level1_0" / "test"
        p2.mkdir(parents=True)
        test_file2 = p2 / "test.txt"
        with open(test_file2, "w") as f:
            f.write("test")

        path1 = self.test_path1
        path2 = self.test_path2

        path_mappings = [
            PathMapping(PurePath("test/abc"), path1),
            PathMapping(PurePath("test"), path2),
        ]
        self.assertRaises(
            AssertionError, lambda: hasher_content_only.hash(path_mappings)
        )


if __name__ == "__main__":
    unittest.main()
