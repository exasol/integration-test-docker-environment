from datetime import datetime
from enum import (
    Enum,
    auto,
)
from typing import (
    Any,
    Optional,
)

from exasol_integration_test_docker_environment.lib.base.info import Info


class ImageState(Enum):
    NOT_EXISTING = auto()
    # After analyze phase or if build phase did touch the image
    NEEDS_TO_BE_BUILD = auto()
    TARGET_LOCALLY_AVAILABLE = auto()
    SOURCE_LOCALLY_AVAILABLE = auto()
    REMOTE_AVAILABLE = auto()
    CAN_BE_LOADED = auto()
    # After build phase
    WAS_BUILD = auto()
    USED_LOCAL = auto()
    WAS_PULLED = auto()
    WAS_LOADED = auto()
    WAS_TAGED = auto()


class ImageDescription:
    def __init__(
        self,
        dockerfile: str,
        image_changing_build_arguments: dict[str, Any],
        transparent_build_arguments: dict[str, Any],
        mapping_of_build_files_and_directories: dict[str, str],
    ) -> None:
        self.transparent_build_arguments = transparent_build_arguments
        self.image_changing_build_arguments = image_changing_build_arguments
        self.mapping_of_build_files_and_directories = (
            mapping_of_build_files_and_directories
        )
        self.dockerfile = dockerfile

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__})"


class ImageInfo(Info):
    DOCKER_TAG_LENGTH_LIMIT = 128
    MAX_TAG_SURPLUS = 30

    def __init__(
        self,
        source_repository_name: str,
        target_repository_name: str,
        source_tag: str,
        target_tag: str,
        hash_value: str,
        commit: str,
        image_description: Optional[ImageDescription],
        build_name: str = "",
        build_date_time: datetime = datetime.utcnow(),
        image_state: Optional[ImageState] = ImageState.NOT_EXISTING,
        depends_on_images: Optional[dict[str, "ImageInfo"]] = None,
    ) -> None:
        self.build_name = build_name
        self.date_time = str(build_date_time)
        self.commit = commit
        self.target_repository_name = target_repository_name
        self.source_repository_name = source_repository_name
        self.image_description = image_description
        self.image_state: Optional[str] = None
        if isinstance(image_state, ImageState):
            self.image_state = image_state.name
        elif isinstance(image_state, str):
            self.image_state = ImageState[image_state].name
        elif image_state is not None:
            raise TypeError(f"{type(image_state)} for image_state not supported")
        self.depends_on_images = depends_on_images
        self.source_tag = source_tag
        self.target_tag = target_tag
        self.hash = hash_value
        self.check_complete_tag_length(self.source_tag)
        self.check_complete_tag_length(self.target_tag)

    def check_complete_tag_length(self, tag):
        complete_tag_length_limit = self.DOCKER_TAG_LENGTH_LIMIT + self.MAX_TAG_SURPLUS
        complete_tag = self._create_complete_tag(tag)
        if len(complete_tag) > complete_tag_length_limit:
            raise Exception(
                f"Complete Tag to long by {len(complete_tag) - complete_tag_length_limit}:  {complete_tag}"
            )

    def get_target_complete_name(self):
        return f"{self.target_repository_name}:{self.get_target_complete_tag()}"

    def get_source_complete_name(self):
        return f"{self.source_repository_name}:{self.get_source_complete_tag()}"

    def get_source_complete_tag(self):
        return self._create_truncated_complete_tag(self.source_tag)

    def get_target_complete_tag(self):
        return self._create_truncated_complete_tag(self.target_tag)

    def _create_truncated_complete_tag(self, tag: str) -> str:
        # we must truncate the tag to 128 characters, because this is the limit of docker tags
        # refer here https://docs.docker.com/engine/reference/commandline/tag/
        complete_tag = self._create_complete_tag(tag)
        truncated_tag = complete_tag[:128]
        return truncated_tag

    def _create_complete_tag(self, tag):
        if self.hash == "":
            return f"{tag}"
        else:
            return f"{tag}_{self.hash}"
