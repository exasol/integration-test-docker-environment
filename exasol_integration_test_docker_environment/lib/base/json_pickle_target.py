from pathlib import Path
from typing import (
    Any,
    Optional,
)

import jsonpickle
from luigi import LocalTarget


class JsonPickleTarget(LocalTarget):

    def __init__(self, path: Path, is_tmp: bool = False) -> None:
        super().__init__(path=str(path), is_tmp=is_tmp)

    def write(self, obj: Any, indent: Optional[int] = None):
        jsonpickle.set_preferred_backend("simplejson")
        jsonpickle.set_encoder_options("simplejson", indent=indent)
        json_str = jsonpickle.encode(obj)
        with self.open("w") as f:
            f.write(json_str)

    def read(self):
        jsonpickle.set_preferred_backend("simplejson")
        with self.open("r") as f:
            json_str = f.read()
            obj = jsonpickle.decode(json_str)
            return obj
