import os
import shutil
import tempfile
import unittest

from exasol_integration_test_docker_environment.lib.docker.images.create.utils.file_directory_list_hasher import (
    FileDirectoryListHasher,
    PathMapping,
)


class TestSymlinkLoops(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp() + "/" + self.__class__.__name__
        self.temp_dir_dummy = tempfile.mkdtemp()

    def generate_test_dir(self, with_symlink_loop):
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
                            "/level0/level1_{}/level2_{}/level3_{}/level4_{}/".format(
                                i1,
                                i2,
                                i3,
                                i4,
                            )
                        )
                        os.makedirs(self.temp_dir + path)
                        os.makedirs(self.temp_dir + path + "test")
                        for i5 in range(level5):
                            file = f"{path}/level5_file_{i5}"
                            with open(self.temp_dir + file, mode="w") as f:
                                f.write(file)

        path = "/level0/level1_{}/level2_{}/level3_{}/level4_{}/".format(
            level1 - 1,
            level2 - 1,
            level3 - 1,
            level4 - 1,
        )
        dest_path = "/level0/level1_%s" % (level1 - 1)

        if with_symlink_loop:
            os.symlink(
                self.temp_dir + dest_path, self.temp_dir + f"{path}/evil_symlink"
            )
        return self.temp_dir + f"{path}/evil_symlink"

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        shutil.rmtree(self.temp_dir_dummy)

    def test_symlink_detection(self):
        self.generate_test_dir(True)
        hasher = FileDirectoryListHasher(
            hashfunc="sha256",
            hash_directory_names=True,
            hash_file_names=True,
            followlinks=True,
        )
        exception_thrown = False
        try:
            hash = hasher.hash(
                [PathMapping(destination=self.__class__.__name__, source=self.temp_dir)]
            )
        except OSError as e:
            if "contains symlink loops" in str(e):
                exception_thrown = True
        assert exception_thrown

    def test_symlink_detection_size(self):
        self.generate_test_dir(True)
        hasher = FileDirectoryListHasher(
            hashfunc="sha256",
            hash_directory_names=True,
            hash_file_names=True,
            followlinks=True,
            max_characters_paths=100,
        )
        exception_thrown = False
        try:
            hash = hasher.hash(
                [PathMapping(destination=self.__class__.__name__, source=self.temp_dir)]
            )
        except OSError as e:
            if "Walking through too many directories." in str(e):
                exception_thrown = True
        assert exception_thrown

    def test_symlink_no_loop(self):
        symlink_dest = self.generate_test_dir(False)
        os.symlink(self.temp_dir_dummy, symlink_dest)
        hasher = FileDirectoryListHasher(
            hashfunc="sha256",
            hash_directory_names=True,
            hash_file_names=True,
            followlinks=True,
        )
        hash = hasher.hash(
            [PathMapping(destination=self.__class__.__name__, source=self.temp_dir)]
        )


if __name__ == "__main__":
    unittest.main()
