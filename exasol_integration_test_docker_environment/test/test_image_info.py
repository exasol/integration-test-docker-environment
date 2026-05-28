import unittest

from exasol_integration_test_docker_environment.lib.docker.images.image_info import (
    ImageDescription,
    ImageInfo,
    Platform,
)


class ImageInfoTest(unittest.TestCase):
    def _create_image_info(self, build_name: str = "") -> ImageInfo:
        return ImageInfo(
            source_repository_name="repo",
            target_repository_name="repo",
            source_tag="flavor-goal",
            target_tag="flavor-goal",
            hash_value="HASH",
            commit="commit",
            image_description=ImageDescription(
                dockerfile="Dockerfile",
                image_changing_build_arguments={},
                transparent_build_arguments={},
                mapping_of_build_files_and_directories={},
                additional_resources={},
            ),
            build_name=build_name,
            platform=Platform.X64,
        )

    def test_source_tag_keeps_hash(self):
        image_info = self._create_image_info(build_name="BUILD")
        self.assertEqual("flavor-goal_x64_HASH", image_info.get_source_complete_tag())
        self.assertEqual(
            "repo:flavor-goal_x64_HASH", image_info.get_source_complete_name()
        )

    def test_target_tag_uses_build_name_when_set(self):
        image_info = self._create_image_info(build_name="BUILD")
        self.assertEqual("flavor-goal_x64_BUILD", image_info.get_target_complete_tag())
        self.assertEqual(
            "repo:flavor-goal_x64_BUILD", image_info.get_target_complete_name()
        )

    def test_target_tag_falls_back_to_hash_when_build_name_missing(self):
        image_info = self._create_image_info()
        self.assertEqual("flavor-goal_x64_HASH", image_info.get_target_complete_tag())


if __name__ == "__main__":
    unittest.main()
