from enum import (
    Enum,
    auto,
)


class TaskState(Enum):
    NONE = auto()
    INIT = auto()
    AFTER_INIT = auto()
    RUN = auto()
    FINISHED = auto()
    CLEANUP = auto()
    CLEANED = auto()
    ERROR = auto()
