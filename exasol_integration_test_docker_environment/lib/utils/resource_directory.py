import importlib
import logging
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Optional

import importlib_resources as ir

LOG = logging.getLogger("resource_directory")


def _copy_importlib_resources_file(
    src_file: ir.abc.Traversable, target_file: Path
) -> None:
    """
    Uses a given source path "src_file" given as an importlib_resources.abc.Traversable to copy the file it points to
    into the destination denoted by target_path.
    :param src_file: Location of the file to be copied, given as importlib_resources.abc.Traversable.
    :param target_file: Path object the location file should be copied to.
    :raises RuntimeError if parameter target_file already exists.
    """
    if src_file.name == "__init__.py":
        LOG.debug(f"Ignoring {src_file} for repository.")
        return
    if target_file.exists():
        error = f"Repository target: {target_file} already exists."
        LOG.error(error)
        raise RuntimeError(error)

    content = src_file.read_bytes()
    with open(target_file, "wb") as file:
        file.write(content)


def _copy_importlib_resources_dir_tree(
    src_path: ir.abc.Traversable, target_path: Path
) -> None:
    """
    Uses a given source path "scr_path" given as an importlib_resources.abc.Traversable to copy all files/directories
    in the directory tree whose root is scr_path into target_path.
    :param src_path: Root of the dir tree to be copied, given as importlib_resources.abc.Traversable.
    :param target_path: Path object the dir tree should be copied to.
    :raises RuntimeError if parameter target_file already exists.
    """
    if not target_path.exists():
        target_path.mkdir()
    for file in src_path.iterdir():
        file_target = target_path / file.name
        if file.is_file():
            _copy_importlib_resources_file(file, file_target)
        else:
            file_target.mkdir(exist_ok=True)
            _copy_importlib_resources_dir_tree(file, file_target)


class ResourceDirectory:
    """
    Copies all files stored within the given package (resource_package) into a temporary directory
    and yields the directory name.
    :resource_package The module whose content should be copied to a temporary directory.
    """

    def __init__(self, resource_package: ModuleType):
        # We need to transform the module to a string and later back to a module
        # because this class will be pickled by luigi and modules are not supported for serialization
        self._resource_package_str = resource_package.__name__
        self._tmp_directory: Optional[tempfile.TemporaryDirectory] = None

    @property
    def tmp_directory(self):
        if self._tmp_directory is not None:
            return self._tmp_directory.name
        else:
            return None

    def create(self) -> str:
        self._tmp_directory = tempfile.TemporaryDirectory()
        assert self._tmp_directory
        source_path = ir.files(self._resource_package_str)
        LOG.debug(
            f"Copying resource package: '{self._resource_package_str}' to '{self._tmp_directory.name}'"
        )
        _copy_importlib_resources_dir_tree(source_path, Path(self._tmp_directory.name))
        return self._tmp_directory.name

    def cleanup(self):
        if self._tmp_directory is not None:
            self._tmp_directory.cleanup()
            self._tmp_directory = None

    def __enter__(self):
        return self.create()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
