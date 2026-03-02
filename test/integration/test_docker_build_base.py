import shutil
from pathlib import Path

import luigi
import pytest
from luigi import Parameter

from exasol_integration_test_docker_environment.lib.base.run_task import (
    generate_root_task,
)
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.docker.images.clean.clean_images import (
    CleanImagesStartingWith,
)
from exasol_integration_test_docker_environment.lib.docker.images.create.docker_build_base import (
    DockerBuildBase,
)
from exasol_integration_test_docker_environment.lib.docker.images.create.docker_image_analyze_task import (
    DockerAnalyzeImageTask,
)
from exasol_integration_test_docker_environment.lib.docker.images.image_info import (
    Platform,
)
from exasol_integration_test_docker_environment.lib.docker.images.utils import (
    find_images_by_tag,
)


class TestDockerBuildBaseTestAnalyzeImage(DockerAnalyzeImageTask):
    task_name = Parameter()
    add_resources = luigi.DictParameter(default={})

    def get_target_repository_name(self) -> str:
        return "exasol-test-docker-build-base"

    def get_source_repository_name(self) -> str:
        return "exasol-test-docker-build-base"

    def get_source_image_tag(self):
        return self.task_name

    def get_target_image_tag(self):
        return self.task_name

    def get_mapping_of_build_files_and_directories(self):
        return {}

    def get_additional_resources(self) -> dict[str, str]:
        return dict(self.add_resources)

    def get_dockerfile(self):
        script_dir = Path(__file__).resolve().parent
        dockerfile_path = Path(
            script_dir, "resources/test_docker_build_base/test_analyze_image/Dockerfile"
        )
        return dockerfile_path

    def is_rebuild_requested(self) -> bool:
        return False


class TestDockerBuildBase(DockerBuildBase):
    goals: list[str] = luigi.ListParameter(default=[])
    add_resources: dict[str, str] = luigi.DictParameter(default={})

    def get_goal_class_map(self) -> dict[str, DockerAnalyzeImageTask]:
        goal_class_map: dict[str, DockerAnalyzeImageTask] = {
            "test-analyze-image-1": self.create_child_task(
                task_class=TestDockerBuildBaseTestAnalyzeImage,
                task_name="test-analyze-image-1",
                add_resources=self.add_resources,
            ),
            "test-analyze-image-2": self.create_child_task(
                TestDockerBuildBaseTestAnalyzeImage, task_name="test-analyze-image-2"
            ),
        }
        return goal_class_map

    def get_default_goals(self) -> set[str]:
        goals = {"test-analyze-image-1"}
        return goals

    def get_goals(self):
        return self.goals

    def run_task(self):
        build_tasks = self.create_build_tasks(False)
        image_infos_futures = yield from self.run_dependencies(build_tasks)
        image_infos = self.get_values_from_futures(image_infos_futures)
        self.return_object(image_infos)


def clean():
    task = generate_root_task(
        task_class=CleanImagesStartingWith,
        starts_with_pattern="exasol-test-docker-build-base",
    )
    luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
    if task._get_tmp_path_for_job().exists():
        shutil.rmtree(str(task._get_tmp_path_for_job()))


@pytest.fixture
def clean_images():
    clean()
    yield
    clean()


def assert_at_least_one_image_exists(prefix: str):
    with ContextDockerClient() as docker_client:
        image_list = find_images_by_tag(docker_client, lambda x: x.startswith(prefix))
        assert len(image_list) >= 1, f"Image with prefix {prefix} not found"
        return image_list


def _run_docker_build_base_task_and_check(expected_img_name: str, **kwargs):
    task = generate_root_task(task_class=TestDockerBuildBase, **kwargs)
    try:
        luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
        return assert_at_least_one_image_exists(expected_img_name)
    finally:
        if task._get_tmp_path_for_job().exists():
            shutil.rmtree(str(task._get_tmp_path_for_job()))


def test_default_parameter(clean_images: None, running_platform: Platform):
    _run_docker_build_base_task_and_check(
        f"exasol-test-docker-build-base:test-analyze-image-1_{running_platform.value}_",
    )


def test_valid_non_default_goal(clean_images: None, running_platform: Platform):
    _run_docker_build_base_task_and_check(
        f"exasol-test-docker-build-base:test-analyze-image-2_{running_platform.value}_",
        goals=["test-analyze-image-2"],
    )


def test_non_valid_non_default_goal(clean_images: None):
    with pytest.raises(Exception, match=r"^Unknown goal\(s\).+"):
        generate_root_task(
            task_class=TestDockerBuildBase, goals=["test-analyze-image-3"]
        )


def check_docker_add_resources_in_image(image: str):
    with ContextDockerClient() as docker_client:
        output_bytes = docker_client.containers.run(
            image,
            command="cat /my_package_file.yaml",
            remove=True,  # Automatically removes the container when it exits
        )
        # Decode the output from bytes to a string
        output = output_bytes.decode("utf-8").strip()
        assert output == "some_package_content"


def test_docker_img_content(clean_images: None):
    img = _run_docker_build_base_task_and_check(
        f"exasol-test-docker-build-base:test-analyze-image-1_",
        add_resources={"my_package_file.yaml": "some_package_content"},
    )
    assert len(img) == 1
    check_docker_add_resources_in_image(img[0])


def test_docker_img_hash_does_not_changes_with_same_resource(clean_images: None):
    add_resources = {"my_package_file.yaml": "some_package_content"}
    exp_image_name = "exasol-test-docker-build-base:test-analyze-image-1_"
    imgs = _run_docker_build_base_task_and_check(
        exp_image_name, add_resources=add_resources
    )
    assert len(imgs) == 1
    imgs = _run_docker_build_base_task_and_check(
        exp_image_name, add_resources=add_resources
    )
    assert len(imgs) == 1


def test_docker_img_hash_changes_if_resource_changes(clean_images: None):
    exp_image_name = "exasol-test-docker-build-base:test-analyze-image-1_"
    imgs = _run_docker_build_base_task_and_check(
        exp_image_name, add_resources={"my_package_file.yaml": "some_package_content_a"}
    )
    assert len(imgs) == 1
    imgs = _run_docker_build_base_task_and_check(
        exp_image_name, add_resources={"my_package_file.yaml": "some_package_content_b"}
    )
    assert len(imgs) == 2
