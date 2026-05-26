import pickle
from pathlib import Path

from exasol_integration_test_docker_environment.lib.base.luigi_compat import (
    LocalTarget,
    NopFormat,
)

FORMAT = NopFormat()


class PickleTarget(LocalTarget):

    def __init__(self, path: Path, is_tmp: bool = False) -> None:
        super().__init__(path=str(path), is_tmp=is_tmp, format=FORMAT)

    def write(self, obj) -> None:
        with self.open("w") as f:
            pickle.dump(obj, f)

    def read(self):
        with self.open("r") as f:
            obj = pickle.load(f)
            return obj
