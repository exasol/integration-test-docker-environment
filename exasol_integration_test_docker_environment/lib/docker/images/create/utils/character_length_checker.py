from pathlib import PurePath
from typing import List


class CharacterLengthChecker:
    """
    This helper class counts the number of character of directory- and file-names.
    If this number exceeds a given limit it raises an exception.
    The goal is to avoid high memory consumption for calculation of huge directories
    which contain many sub-directories/files (broad directory trees) and long names.
    """

    def __init__(
        self,
        root_directory: PurePath,
        max_characters_paths: int,
        count_directory_names: bool,
        count_file_names: bool,
    ):
        self._num_characters = 0
        self._max_characters_paths = max_characters_paths
        self._root_directory = root_directory
        self._count_directory_names = count_directory_names
        self._count_file_names = count_file_names

    def add_and_check(self, directories: List[str], files: List[str]) -> None:
        """
        Adds number of characters of the names of all directories and files to the internal counter
        and applies the check if the internal counter becomes greater than the given limit.
        :param directories Characters of all names of this list will be counted
        :param files Characters of all names of this list will be counted
        raises: OSError if the counted character is greater than the given limit
        """
        if self._count_directory_names:
            self._num_characters += sum([len(d) for d in directories])
        if self._count_file_names:
            self._num_characters += sum([len(f) for f in files])

        if self._num_characters > self._max_characters_paths:
            raise OSError(
                f"Walking through too many directories. Aborting. Please verify: {self._root_directory}"
            )
