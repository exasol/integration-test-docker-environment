import contextlib
import logging
import tempfile
from pathlib import Path
import importlib_resources as ir

LOG = logging.getLogger("resource_directory")


def _copy_importlib_resources_file(src_file: ir.abc.Traversable, target_file: Path) -> None:
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


def _copy_importlib_resources_dir_tree(src_path: ir.abc.Traversable, target_path: Path) -> None:
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


@contextlib.contextmanager
def resource_directory(resource_package):
    """
    Copies all files stored within the given package (resource_package) into a temporary directory
    and yields the directory name.
    :resource_package The module whose content should be copied to a temporary directory.
    """
    with tempfile.TemporaryDirectory() as d:
        source_path = ir.files(resource_package)
        LOG.debug(f"Copying resource package: '{resource_package}' to '{d}'")
        _copy_importlib_resources_dir_tree(source_path, Path(d))
        yield d
