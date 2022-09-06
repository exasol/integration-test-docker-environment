import hashlib
import os
import stat
from dataclasses import dataclass
from multiprocessing import Pool
from pathlib import Path
from typing import List, Callable

import humanfriendly

from exasol_integration_test_docker_environment.lib.docker.images.create.utils.symlink_loop_checker import \
    SymlinkLoopChecker

HASH_FUNCTIONS = {
    'md5': hashlib.md5,
    'sha1': hashlib.sha1,
    'sha256': hashlib.sha256,
    'sha512': hashlib.sha512
}


@dataclass(frozen=True)
class PathMapping:
    destination: str
    source: str


@dataclass(frozen=True)
class DestinationMapping:
    """
    Represents one file/directory found by traversing the source directory tree.
    """
    destination_path: str
    """The path of the file/directory in the destination (including destination_root_path)"""
    source_path: str
    """The path of the file/directory in the source"""
    destination_root_path: str
    """The root of the destination as given in the mapping"""
    is_file: bool
    """Indicates if the entry is a file or directory."""

    def use_for_hashing(self, hash_files: bool, hash_directories: bool) -> bool:
        """
        Returns if this file/directory entry should be used for file hashing, considering parameters
        "hash_files" and "hash_directories".
        """
        if self.is_file:
            return hash_files
        else:
            return hash_directories


@dataclass(frozen=True)
class DirectoryMappingResult:
    """
    Contains all entries found by traversing all mapping directory paths.
    """
    sources: List[str]
    paths_for_hashing: List[DestinationMapping]


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
                                      hash_permissions=hash_permissions)
        self.file_content_hasher = FileContentHasher(hashfunc, blocksize)

    def hash(self, files_and_directories: List[PathMapping]) -> bytes:
        if not isinstance(files_and_directories, List):
            raise Exception("List with paths expected and not '%s' with type %s"
                            % (files_and_directories, type(files_and_directories)))

        directory_mapping_result = self.collect_dest_path_and_src_files(files_and_directories)
        hashes = self.compute_hashes(directory_mapping_result)
        return self._reduce_hash(hashes)

    def check_no_duplicate_destinations(self, mappings: List[DestinationMapping]) -> None:
        """
        Verify that there are no duplicate mappings to same destination.
        This can happen, if the destination of two mappings are equal and the two sources contains the same sub-path
        structure; or if the destination of two mappings is the same file.
        """
        destination_paths = [p.destination_path for p in mappings]
        if len(set(destination_paths)) != len(destination_paths):
            raise AssertionError(f"Directory content for hashing contains duplicates: {destination_paths}")

    def collect_dest_path_and_src_files(self, files_and_directories: List[PathMapping]) -> DirectoryMappingResult:
        """
        Traverse the source paths of all mappings and assemble two lists:
        1) Destination paths-names (for Hashing):
            Mapping of source file/directory -> destination of file/directory,
            ordered by destination path. List[DestinationMapping].
        2) Source files, ordered by destination path
        Collection is done considering the current configuration
         - for both: excluded_directory/excluded_extensions/excluded_file
         - for 1): hash_file_names/hash_directory_names
        """
        collected_dest_paths: List[DestinationMapping] = list()

        def replace_src_by_dest_path(src: str, dest: str, target: str) -> str:
            if not target.startswith(src):
                raise RuntimeError(f"path target {target} does not start with source: {src}")
            p = Path(target).relative_to(src)
            return str(Path(dest) / p)

        for file_or_directory in files_and_directories:
            source = file_or_directory.source
            destination = file_or_directory.destination

            def handle_directory(directories: List[str]) -> None:
                new_dest_paths_mappings = [DestinationMapping(
                                            destination_path=replace_src_by_dest_path(source, destination, p),
                                            source_path=p,
                                            destination_root_path=destination,
                                            is_file=False) for p in directories]
                collected_dest_paths.extend(new_dest_paths_mappings)

            def handle_files(files: List[str]) -> None:
                collected_dest_paths.extend([DestinationMapping(
                                           destination_path=replace_src_by_dest_path(source, destination, f),
                                           source_path=f,
                                           destination_root_path=destination,
                                           is_file=True) for f in files])

            if os.path.isdir(source):
                self.traverse_directory(source, handle_directory, handle_files)
            elif os.path.isfile(source):
                collected_dest_paths.append(DestinationMapping(destination_path=destination, source_path=source,
                                                               destination_root_path=".", is_file=True))
            else:
                raise FileNotFoundError("Could not find file or directory %s" % source)
        collected_dest_paths.sort(key=lambda x: x.destination)
        self.check_no_duplicate_destinations(collected_dest_paths)

        # Now, after we sorted the collected paths, filter out paths which are not needed for current configuration
        filtered_dest_paths = [d for d in collected_dest_paths
                               if d.use_for_hashing(self.hash_file_names, self.hash_directory_names)]

        collected_src_files = [p.source_path for p in collected_dest_paths if p.is_file]
        return DirectoryMappingResult(sources=collected_src_files, paths_for_hashing=filtered_dest_paths)

    def compute_hashes(self, directory_mapping_result: DirectoryMappingResult) -> List[str]:
        paths_for_hashing = directory_mapping_result.paths_for_hashing
        collected_src_files = directory_mapping_result.sources
        pool = Pool(processes=self.workers)
        dest_path_hashes_future = \
            pool.map_async(self.path_hasher.hash, paths_for_hashing, chunksize=2)
        file_content_hashes_future = \
            pool.map_async(self.file_content_hasher.hash, collected_src_files, chunksize=2)
        hashes = []
        hashes.extend(file_content_hashes_future.get())
        file_path_hashes_of_directories = dest_path_hashes_future.get()
        hashes.extend(file_path_hashes_of_directories)
        return hashes

    def has_excluded_extension(self, f: str):
        return f.split('.')[-1:][0] in self.excluded_extensions

    def is_excluded_file(self, f: str):
        return f in self.excluded_files

    def is_excluded_directory(self, f: str):
        return f in self.excluded_directories

    def traverse_directory(self, directory: str,
                           directory_handler: Callable[[List[str]], None],
                           file_handler: Callable[[List[str]], None]) -> None:

        symlink_loop_checker = SymlinkLoopChecker()
        numCharacters = 0

        for root, dirs, files in os.walk(directory, topdown=True, followlinks=self.followlinks):
            symlink_loop_checker.check_and_add(root)
            new_directories = [os.path.join(root, d) for d in dirs if not self.is_excluded_directory(d)]
            directory_handler(new_directories)
            numCharacters += sum([len(d) for d in new_directories])

            new_files = [os.path.join(root, f) for f in files
                         if not self.is_excluded_file(f) and not self.has_excluded_extension(f)]
            file_handler(new_files)
            numCharacters += sum([len(f) for f in new_files])

            if numCharacters > self.MAX_CHARACTERS_PATHS:
                raise OSError(f"Walking through too many directories. Aborting. Please verify: {directory}")

    def _reduce_hash(self, hashes):
        hasher = self.hash_func()
        for hashvalue in hashes:
            hasher.update(hashvalue)
        return hasher.digest()


class PathHasher:
    def __init__(self, hashfunc: str = 'md5',
                 hash_permissions: bool = False,
                 use_relative_paths: bool = False,):
        self.use_relative_paths = use_relative_paths
        self.hash_permissions = hash_permissions
        self.hash_func = HASH_FUNCTIONS.get(hashfunc)
        if not self.hash_func:
            raise NotImplementedError('{} not implemented.'.format(hashfunc))

    def hash(self, path_mapping: DestinationMapping):
        src_path = Path(path_mapping.source_path)
        dest_path = Path(path_mapping.destination_path)
        dest_root = Path(path_mapping.destination_root_path)
        if self.use_relative_paths and len(path_mapping.destination_root_path) > 0:
            path = dest_path.relative_to(dest_root)
        else:
            path = dest_path
        hasher = self.hash_func()
        hasher.update(str(path).encode('utf-8'))
        if self.hash_permissions:
            stat_result = os.stat(src_path)
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
