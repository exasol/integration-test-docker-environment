from enum import Enum
from sys import stderr

import jsonpickle


class TaskDescription:

    def __init__(self, id: str, representation: str):
        self.representation = representation
        self.id = id

    @property
    def formatted_representation(self):
        representation = self.representation.replace('"', '\\"')
        return f'"{representation}"'

    @property
    def formatted_id(self):
        assert '"' not in self.id
        return f'"{self.id}"'


class DependencyType(Enum):
    requires = (1,)
    dynamic = 2


class DependencyState(Enum):
    requested = 1
    finished = 2


class TaskDependency:

    def __init__(
        self,
        source: TaskDescription,
        target: TaskDescription,
        type: DependencyType,
        index: int,
        state: DependencyState,
    ):
        self.state = state.name
        self.index = index
        self.type = type.name
        self.target = target
        self.source = source

    def to_json(self):
        jsonpickle.set_preferred_backend("simplejson")
        jsonpickle.set_encoder_options("simplejson", sort_keys=True)
        return jsonpickle.encode(self)

    @classmethod
    def from_json(cls, json_string: object) -> object:
        loaded_object = jsonpickle.decode(json_string)
        if not isinstance(loaded_object, cls):
            raise TypeError(
                "Type {} of loaded object does not match {}".format(
                    type(loaded_object), cls
                )
            )
        return loaded_object

    @property
    def formatted(self):
        assert '"' not in str(self)
        return f'"{str(self)}"'

    def __str__(self):
        return (
            f"TaskDependency(source={self.source}, "
            f"target={self.target}, type={self.type}, "
            f"index={self.index}, state={self.state})"
        )
