import shutil
import time
import unittest
from pathlib import Path
from datetime import datetime

import docker
import luigi
from luigi import Parameter, Config

from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import DependencyLoggerBaseTask
from exasol_integration_test_docker_environment.lib.base.json_pickle_parameter import JsonPickleParameter

from typing import Set, Dict

from exasol_integration_test_docker_environment.lib.config.docker_config import target_docker_repository_config, \
    source_docker_repository_config
from exasol_integration_test_docker_environment.lib.docker.images.create.docker_build_base import DockerBuildBase
from exasol_integration_test_docker_environment.lib.docker.images.create.docker_image_analyze_task import \
    DockerAnalyzeImageTask
from exasol_integration_test_docker_environment.lib.docker.images.push.docker_push_parameter import DockerPushParameter
from exasol_integration_test_docker_environment.lib.docker.images.push.push_task_creator_for_build_tasks import \
    PushTaskCreatorFromBuildTasks
from exasol_integration_test_docker_environment.lib.docker.images.clean.clean_images import CleanImagesStartingWith

class TestDockerBuildBaseTestAnalyzeImage(DockerAnalyzeImageTask):

    task_name = Parameter()

    def get_target_repository_name(self) -> str:
        return f"""exasol-test-docker-build-base"""

    def get_source_repository_name(self) -> str:
        return f"""exasol-test-docker-build-base"""

    def get_source_image_tag(self):
        return self.task_name

    def get_target_image_tag(self):
        return self.task_name

    def get_mapping_of_build_files_and_directories(self):
        return {}

    def get_dockerfile(self):
        script_dir = Path(__file__).resolve().parent
        dockerfile_path = Path(script_dir, "resources/test_docker_build_base/test_analyze_image/Dockerfile")
        return dockerfile_path

    def is_rebuild_requested(self) -> bool:
        return False


class TestDockerBuildBase(DockerBuildBase):
    goals = luigi.ListParameter([])

    def get_goal_class_map(self) -> Dict[str, DockerAnalyzeImageTask]:
        goal_class_map = {
                "test-analyze-image-1": TestDockerBuildBaseTestAnalyzeImage(task_name="test-analyze-image-1"),
                "test-analyze-image-2": TestDockerBuildBaseTestAnalyzeImage(task_name="test-analyze-image-2")
                }
        return goal_class_map

    def get_default_goals(self) -> Set[str]:
        goals = {"test-analyze-image-1"}
        return goals

    def get_goals(self):
        return self.goals

    def run_task(self):
        build_tasks = self.create_build_tasks(False)
        image_infos_futures = yield from self.run_dependencies(build_tasks)
        image_infos = self.get_values_from_futures(image_infos_futures)
        self.return_object(image_infos)

class DockerBuildBaseTest(unittest.TestCase):

    def set_job_id(self, task_cls):
        strftime = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
        job_id = f"{strftime}_{task_cls.__name__}"
        config = luigi.configuration.get_config()
        config.set('job_config', 'job_id', job_id)

    def clean(self):
        self.set_job_id(CleanImagesStartingWith)
        task = CleanImagesStartingWith(starts_with_pattern="exasol-test-docker-build-base")
        luigi.build([task], workers=1, local_scheduler=True, log_level="ERROR")
        if task._get_tmp_path_for_job().exists():
            shutil.rmtree(str(task._get_tmp_path_for_job()))

    def setUp(self):
        self.client = docker.from_env()
        self.clean()

    def tearDown(self):
        self.clean()
        self.client.close()

    def test_default_parameter(self):
        self.set_job_id(TestDockerBuildBase)
        task = TestDockerBuildBase()
        luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
        if task._get_tmp_path_for_job().exists():
            shutil.rmtree(str(task._get_tmp_path_for_job()))

    def test_valid_non_default_goal(self):
        self.set_job_id(TestDockerBuildBase)
        task = TestDockerBuildBase(goals=["test-analyze-image-2"])
        luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
        if task._get_tmp_path_for_job().exists():
            shutil.rmtree(str(task._get_tmp_path_for_job()))

    def test_non_valid_non_default_goal(self):
        self.set_job_id(TestDockerBuildBase)
        with self.assertRaises(Exception) as contex:
            task = TestDockerBuildBase(goals=["test-analyze-image-3"])
        self.assertIn("Unknown goal(s)",str(contex.exception))


if __name__ == '__main__':
    unittest.main()
