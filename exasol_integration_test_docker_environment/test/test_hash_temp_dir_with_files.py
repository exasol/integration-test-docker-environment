import base64
import os
import tempfile
import unittest
from pathlib import Path

from exasol_integration_test_docker_environment.lib.docker.images.create.utils.file_directory_list_hasher import \
    FileDirectoryListHasher, PathMapping


class HashTempDirTest(unittest.TestCase):
    
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
        """
        hasher_content_only = \
            FileDirectoryListHasher(followlinks=True,
                                    hashfunc="sha256",
                                    hash_file_names=True,
                                    hash_directory_names=True,
                                    hash_permissions=True)
        test_file1 = f"{self.test_path1}/test.txt"
        with open(test_file1, "w") as f:
            f.write("test")
            hash1_content_only = hasher_content_only.hash([PathMapping("test.txt", test_file1)])

        test_file2 = f"{self.test_path2}/test.txt"
        with open(test_file2, "w") as f:
            f.write("test")
            hash2_content_only = hasher_content_only.hash([PathMapping("test.txt", test_file2)])

        ascii_hash1_content_only = base64.b32encode(hash1_content_only).decode("ASCII")
        ascii_hash2_content_only = base64.b32encode(hash2_content_only).decode("ASCII")
        self.assertEqual(ascii_hash1_content_only, ascii_hash2_content_only)

    def test_file_name_with_relative_path_in_same_sub_path(self):
        """
        Test that hashing of same files in different paths, but under same subpath, gives same result
        """
        hasher_content_only = \
            FileDirectoryListHasher(followlinks=True,
                                    hashfunc="sha256",
                                    hash_file_names=True,
                                    hash_directory_names=True,
                                    hash_permissions=True)
        p1 = self.test_path1 / "level0"
        p1.mkdir()
        test_file1 = p1 / "test.txt"
        with open(test_file1, "w") as f:
            f.write("test")
            hash1_content_only = hasher_content_only.hash([PathMapping("level0/test.txt", str(test_file1))])

        p2 = self.test_path2 / "level0"
        p2.mkdir()
        test_file2 = p2 / "test.txt"
        with open(test_file2, "w") as f:
            f.write("test")
            hash2_content_only = hasher_content_only.hash([PathMapping("level0/test.txt", str(test_file2))])

        ascii_hash1_content_only = base64.b32encode(hash1_content_only).decode("ASCII")
        ascii_hash2_content_only = base64.b32encode(hash2_content_only).decode("ASCII")
        self.assertEqual(ascii_hash1_content_only, ascii_hash2_content_only)

    def test_file_name_with_relative_path_in_different_sub_path(self):
        """
        Test that hashing of same files in different paths, and different subpaths, gives different result
        """
        hasher_content_only = \
            FileDirectoryListHasher(followlinks=True,
                                    hashfunc="sha256",
                                    hash_file_names=True,
                                    hash_directory_names=True,
                                    hash_permissions=True)
        p1 = self.test_path1 / "level0"
        p1.mkdir()
        test_file1 = p1 / "test.txt"
        with open(test_file1, "w") as f:
            f.write("test")
            hash1_content_only = hasher_content_only.hash([PathMapping("level0/test.txt", str(test_file1))])

        p2 = self.test_path2 / "level0" / "level1_0"
        p2.mkdir(parents=True)
        test_file2 = p2 / "test.txt"

        with open(test_file2, "w") as f:
            f.write("test")
            hash2_content_only = hasher_content_only.hash([PathMapping("level0/level1_0/test.txt",
                                                                       str(test_file2))])

        ascii_hash1_content_only = base64.b32encode(hash1_content_only).decode("ASCII")
        ascii_hash2_content_only = base64.b32encode(hash2_content_only).decode("ASCII")
        self.assertNotEqual(ascii_hash1_content_only, ascii_hash2_content_only)

    def test_file_name_with_relative_path_in_relative_path_as_argument(self):
        """
        Test that hashing of same files in different paths, gives same result, using relative paths as argument
        """
        hasher_content_only = \
            FileDirectoryListHasher(followlinks=True,
                                    hashfunc="sha256",
                                    hash_file_names=True,
                                    hash_directory_names=True,
                                    hash_permissions=True)
        test_file = f"test.txt"
        old_pwd = os.getcwd()
        os.chdir(self.test_path1)
        with open(test_file, "w") as f:
            f.write("test")
            hash1_content_only = hasher_content_only.hash([PathMapping("test.txt", test_file)])
        os.chdir(self.test_path2)

        with open(test_file, "w") as f:
            f.write("test")
            hash2_content_only = hasher_content_only.hash([PathMapping("test.txt", test_file)])
        os.chdir(old_pwd)
        ascii_hash1_content_only = base64.b32encode(hash1_content_only).decode("ASCII")
        ascii_hash2_content_only = base64.b32encode(hash2_content_only).decode("ASCII")
        self.assertEqual(ascii_hash1_content_only, ascii_hash2_content_only)

    def test_duplicated_file_mapping_raises_exception(self):
        """
        Test that a duplicated mapping raises an exception.
        """
        hasher_content_only = \
            FileDirectoryListHasher(followlinks=True,
                                    hashfunc="sha256",
                                    hash_file_names=True,
                                    hash_directory_names=True,
                                    hash_permissions=True)
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

        path_mappings = [PathMapping("test.txt", str(test_file1)), PathMapping("test.txt", str(test_file2))]
        self.assertRaises(AssertionError, lambda: hasher_content_only.hash(path_mappings))

    def test_duplicated_path_mapping_raises_exception(self):
        """
        Test that a duplicated mapping raises an exception.
        """
        hasher_content_only = \
            FileDirectoryListHasher(followlinks=True,
                                    hashfunc="sha256",
                                    hash_file_names=True,
                                    hash_directory_names=True,
                                    hash_permissions=True)

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
        path_mappings = [PathMapping("test", str(path1)), PathMapping("test", str(path2))]
        self.assertRaises(AssertionError, lambda: hasher_content_only.hash(path_mappings))

    def test_duplicated_path_mapping_with_subpath_raises_exception(self):
        """
        Test that a duplicated mapping raises an exception.
        """
        hasher_content_only = \
            FileDirectoryListHasher(followlinks=True,
                                    hashfunc="sha256",
                                    hash_file_names=True,
                                    hash_directory_names=True,
                                    hash_permissions=True)

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
        destination_path = "test/abc"
        path_mappings = [PathMapping(destination_path, str(path1)), PathMapping(destination_path, str(path2))]
        self.assertRaises(AssertionError, lambda: hasher_content_only.hash(path_mappings))

    def test_duplicated_path_mapping_with_destination_subpath_raises_exception(self):
        """
        Test that a duplicated mapping raises an exception.
        In this scenario we have one path which maps to a destination containing a subpath;
        the second path maps to root destination of the first, but contains the subdirectory of the first in the
        source directory.
        """
        hasher_content_only = \
            FileDirectoryListHasher(followlinks=True,
                                    hashfunc="sha256",
                                    hash_file_names=True,
                                    hash_directory_names=True,
                                    hash_permissions=True)

        p1 = self.test_path1 / "abc" / "level1_0" / "test"
        test_file1 = p1 / "test.txt"
        p1.mkdir(parents=True)
        with open(test_file1, "w") as f:
            f.write("test")
        p2 = self.test_path2 / "level1_0" / "test"
        p2.mkdir(parents=True)
        test_file2 = p2 / "test.txt"
        with open(test_file2, "w") as f:
            f.write("test")

        path1 = self.test_path1
        path2 = self.test_path2

        path_mappings = [PathMapping("test", str(path1)), PathMapping("test/abc", str(path2))]
        self.assertRaises(AssertionError, lambda: hasher_content_only.hash(path_mappings))

if __name__ == '__main__':
    unittest.main()
