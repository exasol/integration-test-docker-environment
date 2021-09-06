from enum import Enum


class TaskState(Enum):
    NONE = 0,
    INIT = 1,
    AFTER_INIT =6,
    RUN = 2,
    FINISHED = 3,
    CLEANUP = 4,
    CLEANED = 5
    ERROR = 7
