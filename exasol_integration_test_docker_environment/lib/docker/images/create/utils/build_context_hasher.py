import base64
import hashlib
from pathlib import (
    Path,
    PurePath,
)

# TODO add hash config to the hash
from exasol_integration_test_docker_environment.lib.docker.images.create.utils.file_directory_list_hasher import (
    FileDirectoryListHasher,
    PathMapping,
)
from exasol_integration_test_docker_environment.lib.docker.images.image_info import (
    ImageDescription,
    ImageInfo,
)


class BuildContextHasher:

    def __init__(self, logger, image_description: ImageDescription) -> None:
        self.image_description = image_description
        self.logger = logger

    def generate_image_hash(self, image_info_of_dependencies: dict[str, ImageInfo]):
        hash_of_build_context = self._generate_build_context_hash()
        final_hash = self._generate_final_hash(
            hash_of_build_context, image_info_of_dependencies
        )
        return self._encode_hash(final_hash)

    def _generate_build_context_hash(self):
        files_directories_list_hasher = FileDirectoryListHasher(
            followlinks=True,
            hashfunc="sha256",
            hash_file_names=True,
            hash_directory_names=True,
            hash_permissions=True,
        )
        files_directories_to_hash = [
            PathMapping(PurePath(destination), Path(source))
            for destination, source in self.image_description.mapping_of_build_files_and_directories.items()
        ]
        # Use only the dockerfile itself for hashing. In order to accomplish that,
        # set the dockerfile only as destination in the mapping
        dockerfile = Path(self.image_description.dockerfile).name
        files_directories_to_hash.append(
            PathMapping(PurePath(dockerfile), Path(self.image_description.dockerfile))
        )
        self.logger.debug("files_directories_list_hasher %s", files_directories_to_hash)
        hash_of_build_context = files_directories_list_hasher.hash(
            files_directories_to_hash
        )
        self.logger.debug(
            "hash_of_build_context %s", self._encode_hash(hash_of_build_context)
        )
        return hash_of_build_context

    def _generate_final_hash(
        self,
        hash_of_build_context: bytes,
        image_info_of_dependencies: dict[str, ImageInfo],
    ):
        hasher = hashlib.sha256()
        self.add_image_changing_build_arguments(hasher)
        self.add_dependencies(hasher, image_info_of_dependencies)
        hasher.update(hash_of_build_context)
        final_hash = hasher.digest()
        return final_hash

    def add_dependencies(
        self, hasher, image_info_of_dependencies: dict[str, ImageInfo]
    ):
        hashes_of_dependencies = [
            (key, image_info.hash)
            for key, image_info in image_info_of_dependencies.items()
        ]
        hashes_to_hash = sorted(hashes_of_dependencies, key=lambda t: t[0])
        self.logger.debug("hashes_to_hash %s", hashes_to_hash)
        for key, image_name in hashes_to_hash:
            hasher.update(key.encode("utf-8"))
            hasher.update(image_name.encode("utf-8"))

    def add_image_changing_build_arguments(self, hasher):
        arguments = [
            (key, value)
            for key, value in self.image_description.image_changing_build_arguments.items()
        ]
        sorted_arguemnts = sorted(arguments, key=lambda t: t[0])
        for key, value in sorted_arguemnts:
            hasher.update(key.encode("utf-8"))
            hasher.update(value.encode("utf-8"))

    def _encode_hash(self, hash_of_build_directory):
        base32 = base64.b32encode(hash_of_build_directory)
        ascii = base32.decode("ASCII")
        trim = ascii.replace("=", "")
        return trim
