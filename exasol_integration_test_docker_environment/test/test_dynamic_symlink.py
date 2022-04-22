import tempfile
import unittest
from pathlib import Path
from threading import Thread
from time import sleep
from typing import Tuple

from exasol_integration_test_docker_environment.lib.base.dynamic_symlink import DynamicSymlink


class DynamicSymlinkTest(unittest.TestCase):

    def test_symlink_lifecycle(self):
        """
        Test that dynamic link temporary directory is being removed when object is released
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_target = temp_path / "test"
            dynamic_symlink = DynamicSymlink("test_link")
            with dynamic_symlink.point_to(test_target) as dynamic_symlink_ctx:
                location = dynamic_symlink_ctx.get_symlink_path()
                self.assertTrue(location.parent.exists())
            self.assertTrue(location.parent.exists())
            dynamic_symlink = None
            self.assertFalse(location.parent.exists())

    def test_symlink_update(self):
        """Test that the update of a symlink works as expected"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_target = temp_path / "test"
            dynamic_symlink = DynamicSymlink("test_link")
            with dynamic_symlink.point_to(test_target) as dynamic_symlink_ctx:
                location = dynamic_symlink_ctx.get_symlink_path()
                self.assertTrue(location.parent.exists())
                location.is_symlink()
                assert location.resolve() == test_target
            test_target_2 = temp_path / "test2"
            with dynamic_symlink.point_to(test_target_2) as dynamic_symlink_ctx:
                location = dynamic_symlink_ctx.get_symlink_path()
                self.assertTrue(location.parent.exists())
                location.is_symlink()
                assert location.resolve() == test_target_2

    def test_symlink_update_parallel(self):
        """Test that the using a symlink in parallel works as expected:
           Create one instance of DynamicSymlink and many threads, which use the same instance
           to write to different files using the same symlink.
        """

        def run(test_target_: Path, msgs: Tuple[str]):
            with dynamic_symlink.point_to(test_target_) as dynamic_symlink_ctx:
                location = dynamic_symlink_ctx.get_symlink_path()
                with open(location, "w") as symlink_file:
                    for msg in msgs:
                        sleep(0.05)
                        symlink_file.write(msg)

        NUMBER_THREADS = 20
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            dynamic_symlink = DynamicSymlink("test_link")
            threads = list()
            for i in range(NUMBER_THREADS):
                test_target = temp_path / f"test_{i}"
                thread = Thread(target=run, args=(test_target, ("This", " is", f" from thread {i}")))
                thread.start()
                threads.append(thread)

            [t.join() for t in threads]
            for i in range(NUMBER_THREADS):
                test_target = temp_path / f"test_{i}"
                with open(test_target, "r") as f:
                    result = f.read()
                    self.assertEqual(result, f"This is from thread {i}")


if __name__ == '__main__':
    unittest.main()
