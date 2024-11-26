from enum import (
    Enum,
    auto,
)


class EnvironmentType(Enum):
    docker_db = auto()
    external_db = auto()
