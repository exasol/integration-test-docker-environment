import os


class SymlinkLoopChecker:
    """
    Collects all visited directory inodes in a set and checks for duplicates.
    Can be used to check for symlink loops.
    """

    def __init__(self):
        self._inodes = set()

    def check_and_add(self, directory: str) -> None:
        """
        Checks if given parameter directory has already been added to the internal set of inodes and raises exception
        if found.
        :param directory: The directory which should be checked.
        :raises OSError if the directory already has been passed before.
        """
        stat = os.stat(directory)
        if stat.st_ino > 0 and stat.st_ino in self._inodes:
            raise OSError(
                f"Directory: {directory} contains symlink loops (Symlinks pointing to a parent directory). Please fix!"
            )
        self._inodes.add(stat.st_ino)
