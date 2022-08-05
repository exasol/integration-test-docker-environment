import tempfile
import unittest
from pathlib import Path

from exasol_integration_test_docker_environment.lib.base.persistent_dictionary import PersistentDictionary


DEFAULT_DICT = "dict"


class PersistentDictionaryTest(unittest.TestCase):

    def test_add(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pd = PersistentDictionary(Path(tmpdir) / DEFAULT_DICT)
            pd["default"] = 1
            assert pd["default"] == 1

    def test_remove(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pd = PersistentDictionary(Path(tmpdir) / DEFAULT_DICT)
            pd["default"] = 1
            assert len(pd) == 1
            del pd["default"]
            assert len(pd) == 0

    def test_iter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pd = PersistentDictionary(Path(tmpdir) / DEFAULT_DICT)
            pd["default"] = 1
            pd["another"] = 2

            it = iter(pd)
            first_key = next(it)
            assert ("default", 1) == (first_key, pd[first_key])
            second_key = next(it)
            assert ("another", 2) == (second_key, pd[second_key])


if __name__ == '__main__':
    unittest.main()
