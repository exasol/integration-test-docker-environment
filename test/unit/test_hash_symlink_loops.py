import os
from pathlib import Path

import pytest

from exasol_integration_test_docker_environment.lib.docker.images.create.utils.file_directory_list_hasher import (
    FileDirectoryListHasher,
    PathMapping,
)


def _make_hasher(max_characters_paths: int = -1) -> FileDirectoryListHasher:
    if max_characters_paths == -1:
        return FileDirectoryListHasher(
            hashfunc="sha256",
            hash_directory_names=True,
            hash_file_names=True,
            followlinks=True,
        )
    else:
        return FileDirectoryListHasher(
            hashfunc="sha256",
            hash_directory_names=True,
            hash_file_names=True,
            followlinks=True,
            max_characters_paths=max_characters_paths,
        )


@pytest.fixture
def temp_dirs(tmp_path_factory):
    temp_dir = tmp_path_factory.mktemp("content")
    symlink_dir = tmp_path_factory.mktemp("symlink")
    yield temp_dir, symlink_dir


def _generate_test_dir(temp_dir: Path, with_symlink_loop: bool) -> Path:
    level1 = 5
    level2 = 5
    for i1 in range(level1):
        for i2 in range(level2):
            path = temp_dir / "level0" / f"level1_{i1}" / f"level2_{i2}"
            path.mkdir(parents=True, exist_ok=False)

    target_path = temp_dir / "level0" / "level1_4"
    symlink = target_path / "level2_4" / "evil_symlink"
    if with_symlink_loop:
        os.symlink(target_path, symlink)
    return symlink


def test_symlink_detection(temp_dirs):
    temp_dir, _ = temp_dirs
    _generate_test_dir(temp_dir, with_symlink_loop=True)
    with pytest.raises(OSError, match=r"contains symlink loops"):
        _make_hasher().hash([PathMapping(destination=Path("content"), source=temp_dir)])


def test_symlink_detection_size(temp_dirs):
    temp_dir, _ = temp_dirs
    _generate_test_dir(temp_dir, with_symlink_loop=True)
    with pytest.raises(OSError, match=r"Walking through too many directories."):
        _make_hasher(max_characters_paths=100).hash(
            [PathMapping(destination=Path("content"), source=temp_dir)]
        )


def test_symlink_no_loop(temp_dirs, request):
    temp_dir, temp_dir_dummy = temp_dirs
    symlink_dest = _generate_test_dir(temp_dir, with_symlink_loop=False)
    os.symlink(temp_dir_dummy, symlink_dest)
    _make_hasher().hash([PathMapping(destination=Path("content"), source=temp_dir)])
    # No assertion, just ensures no exception is thrown
