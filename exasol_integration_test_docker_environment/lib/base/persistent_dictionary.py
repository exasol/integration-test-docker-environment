from collections.abc import MutableMapping
from pathlib import Path
from typing import Dict, Any

from exasol_integration_test_docker_environment.lib.base.pickle_target import PickleTarget


class PersistentDictionary(MutableMapping):
    def __init__(self, dict_path: Path):
        self.target = PickleTarget(dict_path)
        self._write(dict())

    def __getitem__(self, key):
        return self._read()[key]

    def __setitem__(self, key, value):
        d = self._read()
        d[key] = value
        self._write(d)

    def __delitem__(self, key):
        d = self._read()
        del d[key]
        self._write(d)

    def __iter__(self):
        d = self._read()
        return iter(d)

    def __len__(self):
        d = self._read()
        return len(d)

    def _read(self) -> Dict[str, Any]:
        return self.target.read()

    def _write(self, d: Dict[str, Any]):
        self.target.write(d)
