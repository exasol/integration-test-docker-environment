import os
import platform
import sys
import unittest

from pathlib import Path
from tempfile import TemporaryDirectory
from exasol_integration_test_docker_environment.lib.base.ssh_access import SshKey


class TestSshKey(unittest.TestCase):
    def test_create_file_and_permissions(self) -> None:
        with TemporaryDirectory() as dir:
            path = Path(dir)
            testee = SshKey.from_folder(path)
            file = path / "id_rsa"
            self.assertTrue(file.exists())
            actual = oct(os.stat(file).st_mode)[-3:]
            expected = "666" if platform.system() == "Windows" else "600"
            self.assertEqual(expected, actual)

    def test_read_existing_file(self):
        with TemporaryDirectory() as dir:
            path = Path(dir)
            testee = SshKey.from_folder(path)
            other = SshKey.from_folder(path)
            self.assertEqual(testee.private, other.private)


if __name__ == '__main__':
    unittest.main()
