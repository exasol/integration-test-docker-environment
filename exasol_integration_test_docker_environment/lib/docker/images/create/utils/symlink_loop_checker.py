import os


class SymlinkLoopChecker:
    def __init__(self):
        self._inodes = set()

    def check_and_add(self, directory: str) -> None:
        stat = os.stat(directory)
        if stat.st_ino > 0 and stat.st_ino in self._inodes:
            raise OSError(
                f"Directory: {directory} contains symlink loops (Symlinks pointing to a parent directory). Please fix!")
        self._inodes.add(stat.st_ino)
