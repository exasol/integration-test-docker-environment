import hashlib
import os
import stat
from dataclasses import dataclass
from multiprocessing import Pool
from pathlib import Path
from typing import List, Tuple, NamedTuple

import humanfriendly

HASH_FUNCTIONS = {
    'md5': hashlib.md5,
    'sha1': hashlib.sha1,
    'sha256': hashlib.sha256,
    'sha512': hashlib.sha512
}


@dataclass
class PathMapping:
    destination: str
    source: str




class RelativePath(NamedTuple):
    root: str
    path: str


class FileDirectoryListHasher:

    def __init__(self,
                 hashfunc: str = 'md5',
                 followlinks: bool = False,
                 hash_file_names: bool = False,
                 hash_permissions: bool = False,
                 hash_directory_names: bool = False,
                 use_relative_paths: bool = False,
                 excluded_directories=None,
                 excluded_files=None,
                 excluded_extensions=None,
                 blocksize: str = "64kb",
                 workers: int = 4,
                 max_characters_paths: int = 500000000
                 ):
        self.MAX_CHARACTERS_PATHS = max_characters_paths
        self.use_relative_paths = use_relative_paths
        self.workers = workers
        self.excluded_files = excluded_files
        self.excluded_extensions = excluded_extensions
        self.excluded_directories = excluded_directories
        self.hash_directory_names = hash_directory_names
        self.hash_permissions = hash_permissions
        self.hash_file_names = hash_file_names
        self.followlinks = followlinks

        self.hash_func = HASH_FUNCTIONS.get(hashfunc)
        if not self.hash_func:
            raise NotImplementedError('{} not implemented.'.format(hashfunc))

        if not self.excluded_files:
            self.excluded_files = []

        if not self.excluded_directories:
            self.excluded_directories = []

        if not self.excluded_extensions:
            self.excluded_extensions = []

        self.path_hasher = PathHasher(hashfunc,
                                      hash_permissions=hash_permissions,
                                      use_relative_paths=use_relative_paths)
        self.file_content_hasher = FileContentHasher(hashfunc, blocksize)

    def hash(self, files_and_directories: List[PathMapping]) -> bytes:
        collected_directories: List[RelativePath] = list()
        collected_files: List[RelativePath] = list()

        if not isinstance(files_and_directories, List):
            raise Exception("List with paths expected and not '%s' with type %s"
                            % (files_and_directories, type(files_and_directories)))
        for file_or_directory in files_and_directories:
            source = file_or_directory.source
            dest = file_or_directory.destination
            if not source.endswith(dest):
                raise AssertionError("source and destination must match. "
                                     "Pathname of destination must be a suffix of source. "
                                     "Otherwise the root path cannot be determined")
            # We calculate the root path based on the information in the mapping, examples:
            # 1. PathMapping(dest="requirements.txt", source="requirements.txt") => root_path = "."
            # 2. PathMapping(dest="test/requirements.txt", source="test/requirements.txt") => root_path = "."
            # 3. PathMapping(dest="requirements.txt", source="test/requirements.txt") => root_path = "./test"
            # 4. PathMapping(dest="requirements.txt", source="/tmp/tmp123/requirements.txt") => root_path = "/tmp/tmp123/"
            root_path = Path(source.rstrip(dest))
            if not root_path.is_dir():
                raise AssertionError(f"calculated root directory '{root_path}' is not valid. Please check mapping:"
                                     f"{file_or_directory}")
            # To keep compatibility we append the slash
            root_path_str = str(root_path) + "/"
            if os.path.isdir(source):
                self.collect_files_and_directories(root_path_str, source, collected_directories, collected_files)
            elif os.path.isfile(source):
                collected_files.append(RelativePath(root_path_str, source))
            else:
                raise FileNotFoundError("Could not find file or directory %s" % source)
        hashes = self.compute_hashes(collected_directories, collected_files)
        return self._reduce_hash(hashes)

    def compute_hashes(self, collected_directories, collected_files):
        pool = Pool(processes=self.workers)
        if self.hash_directory_names:
            file_path_hashes_of_directories_future = \
                pool.map_async(self.path_hasher.hash, collected_directories, chunksize=2)
        else:
            file_path_hashes_of_directories_future = None
        if self.hash_file_names:
            file_path_hashes_of_files_future = \
                pool.map_async(self.path_hasher.hash, collected_files, chunksize=2)
        else:
            file_path_hashes_of_files_future = None
        file_list = [path for root, path in collected_files]
        file_content_hashes_future = \
            pool.map_async(self.file_content_hasher.hash, file_list, chunksize=2)
        hashes = []
        hashes.extend(file_content_hashes_future.get())
        if self.hash_directory_names:
            file_path_hashes_of_directories = file_path_hashes_of_directories_future.get()
            hashes.extend(file_path_hashes_of_directories)
        if self.hash_file_names:
            file_path_hashes_of_files = file_path_hashes_of_files_future.get()
            hashes.extend(file_path_hashes_of_files)
        return hashes

    def has_excluded_extension(self, f: str):
        return f.split('.')[-1:][0] in self.excluded_extensions

    def is_excluded_file(self, f: str):
        return f in self.excluded_files

    def is_excluded_directory(self, f: str):
        return f in self.excluded_directories

    def collect_files_and_directories(
            self, root_dir: str, directory: str,
            collected_directories: List[RelativePath],
            collected_files: List[RelativePath]):
        tmp_collected_directories = list()
        tmp_collected_files = list()
        if self.hash_directory_names:
            tmp_collected_directories.append(RelativePath(root_dir, str(directory)))
        inodes = set()
        numCharacters = 0

        for root, dirs, files in os.walk(directory, topdown=True, followlinks=self.followlinks):
            stat = os.stat(root)
            if stat.st_ino > 0 and stat.st_ino in inodes:
                raise OSError(
                    f"Directory: {directory} contains symlink loops (Symlinks pointing to a parent directory). Please fix!")
            inodes.add(stat.st_ino)

            if self.hash_directory_names:
                new_directories = [d for d in dirs if not self.is_excluded_directory(d)]
                tmp_collected_directories.extend([RelativePath(root_dir, os.path.join(root, d))
                                                  for d in new_directories])
                numCharacters += sum([len(d) for d in new_directories])

            new_files = [f for f in files
                         if not self.is_excluded_file(f) and not self.has_excluded_extension(f)]
            tmp_collected_files.extend([RelativePath(root_dir, os.path.join(root, f)) for f in new_files])
            numCharacters += sum([len(f) for f in new_files])

            if numCharacters > self.MAX_CHARACTERS_PATHS:
                raise OSError(f"Walking through too many directories. Aborting. Please verify: {directory}")

        collected_directories.extend(sorted(tmp_collected_directories, key=lambda x: x.path))
        collected_files.extend(sorted(tmp_collected_files, key=lambda x: x.path))

    def _reduce_hash(self, hashes):
        hasher = self.hash_func()
        for hashvalue in hashes:
            hasher.update(hashvalue)
        return hasher.digest()


class PathHasher:
    def __init__(self, hashfunc: str = 'md5',
                 hash_permissions: bool = False,
                 use_relative_paths: bool = False, ):
        self.use_relative_paths = use_relative_paths
        self.hash_permissions = hash_permissions
        self.hash_func = HASH_FUNCTIONS.get(hashfunc)
        if not self.hash_func:
            raise NotImplementedError('{} not implemented.'.format(hashfunc))

    def hash(self, root_path_pair: Tuple[str, str]):
        original_path = Path(root_path_pair[1])
        if self.use_relative_paths and len(root_path_pair[0]) > 0:
            path = original_path.relative_to(Path(root_path_pair[0]))
        else:
            path = original_path
        hasher = self.hash_func()
        hasher.update(str(path).encode('utf-8'))
        if self.hash_permissions:
            stat_result = os.stat(original_path)
            # we only check the executable right of the user, because git only remembers this
            user_has_executable_rights = stat.S_IXUSR & stat_result[stat.ST_MODE]
            hasher.update(str(user_has_executable_rights).encode("utf-8"))
        return hasher.digest()


class FileContentHasher:

    def __init__(self, hashfunc: str = 'md5', blocksize: str = "64kb"):
        self.blocksize = humanfriendly.parse_size(blocksize)
        self.hash_func = HASH_FUNCTIONS.get(hashfunc)
        if not self.hash_func:
            raise NotImplementedError('{} not implemented.'.format(hashfunc))

    def hash(self, filepath: str):
        hasher = self.hash_func()
        with open(os.path.join(filepath), 'rb') as fp:
            while True:
                data = fp.read(self.blocksize)
                if not data:
                    break
                hasher.update(data)
        return hasher.digest()
