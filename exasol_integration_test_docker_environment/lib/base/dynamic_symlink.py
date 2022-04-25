import os
import tempfile
from pathlib import Path
from threading import Lock


class DynamicSymlinkContextManager(object):
    """
    Creates a thread-safe symlink during it's context lifetime.
    """
    def __init__(self, symlink_path: Path, target_path: Path, lock: Lock):
        self.symlink_path = symlink_path
        self.target_path = target_path
        self.lock = lock

    def __enter__(self):
        print(f"DynamicSymlinkContextManager - enter. Setting symlink to {self.target_path}")
        self.lock.acquire()
        if self.symlink_path.exists():
            raise RuntimeError("Symlink already exists.")
        self.symlink_path.symlink_to(target=self.target_path.absolute(), target_is_directory=False)
        print (f"Symlink result:{os.readlink(self.symlink_path)}")
        return self

    def __exit__(self, type_, value, traceback):
        print("DynamicSymlinkContextManager - exit")
        self.symlink_path.unlink()
        self.lock.release()

    def get_symlink_path(self):
        return self.symlink_path


class DynamicSymlink(object):
    """"
    Manages a dynamic symlink located under are a new temporary directory.
    The symlink can be updated to point to a new target. It exists then only during the life of the return ContextManager.
    The temporary directory will be automatically deleted when this object is being released.
    """

    def __init__(self, symlink_name: str):
        self.temporary_directory = "/tmp/def"
        #self.temporary_directory = tempfile.TemporaryDirectory()
        self.symlink_path = Path(self.temporary_directory) / symlink_name
        self.lock = Lock()

    def point_to(self, target: Path) -> DynamicSymlinkContextManager:
        return DynamicSymlinkContextManager(self.symlink_path, target, self.lock)

    def __getstate__(self):
        raise NotImplementedError(f"{self.__class__.__name__} is not allowed to be shared among processes. "
                                  f"Because of that, serialization is not supported.")

    def __del__(self):
        pass
        #self.temporary_directory.cleanup()
