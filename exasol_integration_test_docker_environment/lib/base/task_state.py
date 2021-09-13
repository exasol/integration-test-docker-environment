from enum import Enum


class TaskState(Enum):
    NONE = 0,
    INIT = 1,
    AFTER_INIT =2,
    RUN = 3,
    FINISHED = 4,
    CLEANUP = 5,
    CLEANED = 6,
    ERROR = 7
