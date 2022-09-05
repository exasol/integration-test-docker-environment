import base64
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from exasol_integration_test_docker_environment.lib.docker.images.create.utils.file_directory_list_hasher import \
    FileDirectoryListHasher, PathMapping

TEST_FILE = "/tmp/SEFQWEFWQEHDUWEFDGZWGDZWEFDUWESGRFUDWEGFUDWAFGWAZESGFDWZA"


def simple_path_mapping(src: str) -> PathMapping:
    """
    Helper function which maps a directory-path to: PathMapping(directory-name, directory-path),
    e.g. /tmp/tmp123/test1 becomes PathMapping('test1', '/tmp/tmp123/test1')
    """
    p = Path(src)
    return PathMapping(p.name, src)


class HashTempDirTest(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.temp_dir = tempfile.mkdtemp() + "/" + self.__class__.__name__
        self.test_dir1 = self.temp_dir + "/test1"
        self.generate_test_dir(self.test_dir1)
        self.test_dir2 = self.temp_dir + "/test2"
        self.generate_test_dir(self.test_dir2)
        
        self.test_dir3 = self.temp_dir + "/test3"
        os.makedirs(self.test_dir3+"/d") 
        with open(self.test_dir3+"/f", "wt") as f:
            f.write("test")
        
        with open(TEST_FILE, "wt") as f:
            f.write("test")

    @classmethod
    def generate_test_dir(self, test_dir):
        level1 = 5
        level2 = 5
        level3 = 5
        level4 = 5
        level5 = 5
        for i1 in range(level1):
            for i2 in range(level2):
                for i3 in range(level3):
                    for i4 in range(level4):
                        path = "/level0/level1_%s/level2_%s/level3_%s/level4_%s/" \
                               % (i1, i2, i3, i4)
                        os.makedirs(test_dir + path)
                        os.makedirs(test_dir + path + "test")
                        for i5 in range(level5):
                            file = "%s/level5_file_%s" % (path, i5)
                            with open(test_dir + file, mode="wt") as f:
                                f.write(file)

    @classmethod
    def tearDownClass(self):
        os.remove(TEST_FILE)
        shutil.rmtree(self.temp_dir)

    def test_single_character_directory_name(self):
        hasher = FileDirectoryListHasher(hashfunc="sha256",
                                         use_relative_paths=False,
                                         hash_directory_names=True,
                                         hash_file_names=True)
        old_pwd = os.getcwd()
        os.chdir(self.test_dir3)
        hash = hasher.hash([simple_path_mapping(".")])
        ascii_hash = base64.b32encode(hash).decode("ASCII")
        self.assertEqual("LVE2ZFQRMP6QLY43MKMZRHIEHE7KNSUS5LFWVJKPOWMI6JUPZHEQ====", ascii_hash)
        os.chdir(old_pwd)

    def test_file_content_only_fixed_hash(self):
        hasher = FileDirectoryListHasher(hashfunc="sha256",
                                         use_relative_paths=False,
                                         hash_directory_names=False,
                                         hash_file_names=False)
        hash = hasher.hash([simple_path_mapping(TEST_FILE)])
        ascii_hash = base64.b32encode(hash).decode("ASCII")
        self.assertEqual("SVGVUSP5ODM3RPG3GXJFEJTYFGKX67XX7JWHJ6EEDG64L2BCBH2A====", ascii_hash)

    def test_file_with_path(self):
        hasher = FileDirectoryListHasher(hashfunc="sha256",
                                         use_relative_paths=False,
                                         hash_directory_names=True,
                                         hash_file_names=True)
        hash = hasher.hash([simple_path_mapping(TEST_FILE)])
        ascii_hash = base64.b32encode(hash).decode("ASCII")
        self.assertEqual("7D34CBUU2SNSWF3UFM6A7BYFJVV5ZFEY5F6THIMGJY725WC45KEA====", ascii_hash)

    def test_directory_with_relative_paths_fixed_hash(self):
        hasher = FileDirectoryListHasher(hashfunc="sha256",
                                         use_relative_paths=True,
                                         hash_directory_names=True,
                                         hash_file_names=True)
        hash = hasher.hash([simple_path_mapping(self.test_dir1)])
        ascii_hash = base64.b32encode(hash).decode("ASCII")
        self.assertEqual("RX5DGLU5AV6UAEZS3AE6L7WKCYOABQY7ISLX2JYX2GWJ22HH5GYQ====", ascii_hash)

    def test_directory_content_only_fixed_hash(self):
        hasher = FileDirectoryListHasher(hashfunc="sha256",
                                         use_relative_paths=False,
                                         hash_directory_names=False,
                                         hash_file_names=False)
        hash = hasher.hash([PathMapping("level0", f"{self.test_dir1}/level0")])
        ascii_hash = base64.b32encode(hash).decode("ASCII")
        self.assertEqual("TM2V22T326TCTLQ537BZAOR3I5NVHXE6IDJ4TXPCJPTUGDTI5WYQ====", ascii_hash)

    def test_directory_with_relative_paths_equal(self):
        hasher = FileDirectoryListHasher(hashfunc="sha256",
                                         use_relative_paths=True,
                                         hash_directory_names=True,
                                         hash_file_names=True)
        hash1 = hasher.hash([PathMapping("level0", f"{self.test_dir1}/level0")])
        hash2 = hasher.hash([PathMapping("level0", f"{self.test_dir2}/level0")])
        ascii_hash1 = base64.b32encode(hash1).decode("ASCII")
        ascii_hash2 = base64.b32encode(hash2).decode("ASCII")
        self.assertEqual(ascii_hash1, ascii_hash2)

    def test_directory_without_relative_paths_not_equal(self):
        hasher = FileDirectoryListHasher(hashfunc="sha256",
                                         use_relative_paths=False,
                                         hash_directory_names=True,
                                         hash_file_names=True)
        hash1 = hasher.hash([simple_path_mapping(self.test_dir1)])
        hash2 = hasher.hash([simple_path_mapping(self.test_dir2)])
        ascii_hash1 = base64.b32encode(hash1).decode("ASCII")
        ascii_hash2 = base64.b32encode(hash2).decode("ASCII")
        self.assertNotEqual(ascii_hash1, ascii_hash2)

    def test_directory_content_only_equal(self):
        hasher = FileDirectoryListHasher(hashfunc="sha256",
                                         use_relative_paths=False,
                                         hash_directory_names=False,
                                         hash_file_names=False)
        hash1 = hasher.hash([simple_path_mapping(self.test_dir1)])
        hash2 = hasher.hash([simple_path_mapping(self.test_dir2)])
        ascii_hash1 = base64.b32encode(hash1).decode("ASCII")
        ascii_hash2 = base64.b32encode(hash2).decode("ASCII")
        self.assertEqual(ascii_hash1, ascii_hash2)

    def test_directory_relative_paths_equal(self):
        hasher = FileDirectoryListHasher(hashfunc="sha256",
                                         use_relative_paths=True,
                                         hash_directory_names=False,
                                         hash_file_names=False)
        hash1 = hasher.hash([simple_path_mapping(self.test_dir1)])
        hash2 = hasher.hash([simple_path_mapping(self.test_dir2)])
        ascii_hash1 = base64.b32encode(hash1).decode("ASCII")
        ascii_hash2 = base64.b32encode(hash2).decode("ASCII")
        self.assertEqual(ascii_hash1, ascii_hash2)

    def test_directory_content_only_not_equal_to_with_paths(self):
        hasher_content_only = \
            FileDirectoryListHasher(hashfunc="sha256",
                                    use_relative_paths=False,
                                    hash_directory_names=False,
                                    hash_file_names=False)
        hasher_with_paths = \
            FileDirectoryListHasher(hashfunc="sha256",
                                    use_relative_paths=True,
                                    hash_directory_names=True,
                                    hash_file_names=True)
        hash1_content_only = hasher_content_only.hash([simple_path_mapping(self.test_dir1)])
        hash2_with_paths = hasher_with_paths.hash([simple_path_mapping(self.test_dir2)])
        ascii_hash1_content_only = base64.b32encode(hash1_content_only).decode("ASCII")
        ascii_hash2_with_paths = base64.b32encode(hash2_with_paths).decode("ASCII")
        self.assertNotEqual(ascii_hash1_content_only, ascii_hash2_with_paths)

    def test_directory_content_only_not_equal_to_dir_names(self):
        hasher_content_only = \
            FileDirectoryListHasher(hashfunc="sha256",
                                    use_relative_paths=False,
                                    hash_directory_names=False,
                                    hash_file_names=False)
        hasher_with_paths = \
            FileDirectoryListHasher(hashfunc="sha256",
                                    use_relative_paths=False,
                                    hash_directory_names=True,
                                    hash_file_names=False)
        hash1_content_only = hasher_content_only.hash([simple_path_mapping(self.test_dir1)])
        hash2_with_paths = hasher_with_paths.hash([simple_path_mapping(self.test_dir1)])
        ascii_hash1_content_only = base64.b32encode(hash1_content_only).decode("ASCII")
        ascii_hash2_with_paths = base64.b32encode(hash2_with_paths).decode("ASCII")
        self.assertNotEqual(ascii_hash1_content_only, ascii_hash2_with_paths)

    def test_directory_content_only_not_equal_to_file_names(self):
        hasher_content_only = \
            FileDirectoryListHasher(hashfunc="sha256",
                                    use_relative_paths=False,
                                    hash_directory_names=False,
                                    hash_file_names=False)
        hasher_with_paths = \
            FileDirectoryListHasher(hashfunc="sha256",
                                    use_relative_paths=False,
                                    hash_directory_names=False,
                                    hash_file_names=True)
        hash1_content_only = hasher_content_only.hash([simple_path_mapping(self.test_dir1)])
        hash2_with_paths = hasher_with_paths.hash([simple_path_mapping(self.test_dir1)])
        ascii_hash1_content_only = base64.b32encode(hash1_content_only).decode("ASCII")
        ascii_hash2_with_paths = base64.b32encode(hash2_with_paths).decode("ASCII")
        self.assertNotEqual(ascii_hash1_content_only, ascii_hash2_with_paths)

    def test_directory_file_names_not_equal_to_dir_names(self):
        hasher_content_only = \
            FileDirectoryListHasher(hashfunc="sha256",
                                    use_relative_paths=True,
                                    hash_directory_names=False,
                                    hash_file_names=True)
        hasher_with_paths = \
            FileDirectoryListHasher(hashfunc="sha256",
                                    use_relative_paths=True,
                                    hash_directory_names=True,
                                    hash_file_names=False)
        hash1_content_only = hasher_content_only.hash([simple_path_mapping(self.test_dir1)])
        hash2_with_paths = hasher_with_paths.hash([simple_path_mapping(self.test_dir2)])
        ascii_hash1_content_only = base64.b32encode(hash1_content_only).decode("ASCII")
        ascii_hash2_with_paths = base64.b32encode(hash2_with_paths).decode("ASCII")
        self.assertNotEqual(ascii_hash1_content_only, ascii_hash2_with_paths)

    def test_file_name_with_relative_path(self):
        """
        Test that hashing of same files in different paths gives same result
        """
        hasher_content_only = \
            FileDirectoryListHasher(followlinks=True,
                                    hashfunc="sha256",
                                    hash_file_names=True,
                                    hash_directory_names=True,
                                    hash_permissions=True,
                                    use_relative_paths=True)
        test_file1 = f"{self.test_dir1}/test.txt"
        with open(test_file1, "w") as f:
            f.write("test")
            hash1_content_only = hasher_content_only.hash([PathMapping("test.txt", test_file1)])

        test_file2 = f"{self.test_dir2}/test.txt"
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
                                    hash_permissions=True,
                                    use_relative_paths=True)
        test_file1 = f"{self.test_dir1}/level0/test.txt"
        with open(test_file1, "w") as f:
            f.write("test")
            hash1_content_only = hasher_content_only.hash([PathMapping("level0/test.txt", test_file1)])

        test_file2 = f"{self.test_dir2}/level0/test.txt"
        with open(test_file2, "w") as f:
            f.write("test")
            hash2_content_only = hasher_content_only.hash([PathMapping("level0/test.txt", test_file2)])

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
                                    hash_permissions=True,
                                    use_relative_paths=True)
        test_file1 = f"{self.test_dir1}/level0/test.txt"
        with open(test_file1, "w") as f:
            f.write("test")
            hash1_content_only = hasher_content_only.hash([PathMapping("level0/test.txt", test_file1)])

        test_file2 = f"{self.test_dir2}/level0/level1_0/test.txt"
        with open(test_file2, "w") as f:
            f.write("test")
            hash2_content_only = hasher_content_only.hash([PathMapping("level0/level1_0/test.txt", test_file2)])

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
                                    hash_permissions=True,
                                    use_relative_paths=True)
        test_file = f"test.txt"
        old_pwd = os.getcwd()
        os.chdir(self.test_dir1)
        with open(test_file, "w") as f:
            f.write("test")
            hash1_content_only = hasher_content_only.hash([PathMapping("test.txt", test_file)])
        os.chdir(self.test_dir2)

        with open(test_file, "w") as f:
            f.write("test")
            hash2_content_only = hasher_content_only.hash([PathMapping("test.txt", test_file)])
        os.chdir(old_pwd)
        ascii_hash1_content_only = base64.b32encode(hash1_content_only).decode("ASCII")
        ascii_hash2_content_only = base64.b32encode(hash2_content_only).decode("ASCII")
        self.assertEqual(ascii_hash1_content_only, ascii_hash2_content_only)

    def test_invalid_mapping_raises_exception(self):
        """
        Test that an invalid mapping raises an exception.
        Invalid means here that the destination must be a suffix of the source.
        """
        hasher_content_only = \
            FileDirectoryListHasher(followlinks=True,
                                    hashfunc="sha256",
                                    hash_file_names=True,
                                    hash_directory_names=True,
                                    hash_permissions=True,
                                    use_relative_paths=True)
        self.assertRaises(AssertionError, lambda: hasher_content_only.hash([PathMapping("/level_INVALID/level1_0",
                                                                           f"{self.test_dir1}/level0/level1_0")]))


if __name__ == '__main__':
    unittest.main()
