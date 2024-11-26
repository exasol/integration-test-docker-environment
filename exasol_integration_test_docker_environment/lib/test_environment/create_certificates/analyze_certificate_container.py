from typing import (
    Dict,
    Set,
)

import luigi

from exasol_integration_test_docker_environment.lib.config.docker_config import (
    source_docker_repository_config,
    target_docker_repository_config,
)
from exasol_integration_test_docker_environment.lib.docker.images.create.docker_build_base import (
    DockerBuildBase,
)
from exasol_integration_test_docker_environment.lib.docker.images.create.docker_image_analyze_task import (
    DockerAnalyzeImageTask,
)
from exasol_integration_test_docker_environment.lib.docker.images.push.docker_push_parameter import (
    DockerPushParameter,
)
from exasol_integration_test_docker_environment.lib.docker.images.push.push_task_creator_for_build_tasks import (
    PushTaskCreatorFromBuildTasks,
)

TAG_SUFFIX = "certificate_resources"


class AnalyzeCertificateContainer(DockerAnalyzeImageTask):
    certificate_container_root_directory = luigi.Parameter()

    def get_target_repository_name(self) -> str:
        return f"""{target_docker_repository_config().repository_name}"""

    def get_source_repository_name(self) -> str:
        return f"""{source_docker_repository_config().repository_name}"""

    def get_source_image_tag(self):
        if source_docker_repository_config().tag_prefix != "":
            return f"{source_docker_repository_config().tag_prefix}_{TAG_SUFFIX}"
        else:
            return TAG_SUFFIX

    def get_target_image_tag(self):
        if target_docker_repository_config().tag_prefix != "":
            return f"{target_docker_repository_config().tag_prefix}_{TAG_SUFFIX}"
        else:
            return TAG_SUFFIX

    def get_mapping_of_build_files_and_directories(self):
        return {
            "create_certificates.sh": f"{self.certificate_container_root_directory}/create_certificates.sh"
        }

    def get_dockerfile(self):
        return f"{self.certificate_container_root_directory}/Dockerfile"

    def is_rebuild_requested(self) -> bool:
        return False


class DockerCertificateBuildBase(DockerBuildBase):
    GOAL = "certificate-container"
    certificate_container_root_directory = luigi.Parameter()

    def get_goal_class_map(self) -> Dict[str, DockerAnalyzeImageTask]:
        goal_class_map = {
            self.GOAL: self.create_child_task(
                task_class=AnalyzeCertificateContainer,
                certificate_container_root_directory=self.certificate_container_root_directory,
            )
        }
        return goal_class_map

    def get_default_goals(self) -> Set[str]:
        goals = {self.GOAL}
        return goals

    def get_goals(self):
        goals = {self.GOAL}
        return goals


class DockerCertificateContainerBuild(DockerCertificateBuildBase):

    def run_task(self):
        build_tasks = self.create_build_tasks(False)
        image_infos_futures = yield from self.run_dependencies(build_tasks)
        image_infos = self.get_values_from_futures(image_infos_futures)
        self.return_object(image_infos)


class DockerTestContainerPush(DockerCertificateBuildBase, DockerPushParameter):

    def run_task(self):
        build_tasks = self.create_build_tasks(shortcut_build=not self.push_all)
        push_task_creator = PushTaskCreatorFromBuildTasks(self)
        push_tasks = push_task_creator.create_tasks_for_build_tasks(build_tasks)
        image_info_future = yield from self.run_dependencies(push_tasks)
        image_info = self.get_values_from_futures(image_info_future)
        self.return_object(image_info)
