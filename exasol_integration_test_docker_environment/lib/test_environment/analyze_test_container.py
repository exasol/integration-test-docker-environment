from typing import (
    Dict,
    Set,
)

from exasol_integration_test_docker_environment.lib.config.build_config import (
    build_config,
)
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
from exasol_integration_test_docker_environment.lib.test_environment.parameter.test_container_parameter import (
    TestContainerParameter,
)


class AnalyzeTestContainer(DockerAnalyzeImageTask, TestContainerParameter):

    def get_target_repository_name(self) -> str:
        return f"""{target_docker_repository_config().repository_name}"""

    def get_source_repository_name(self) -> str:
        return f"""{source_docker_repository_config().repository_name}"""

    def get_source_image_tag(self):
        if source_docker_repository_config().tag_prefix != "":
            return f"{source_docker_repository_config().tag_prefix}_db-test-container"
        else:
            return f"db-test-container"

    def get_target_image_tag(self):
        if target_docker_repository_config().tag_prefix != "":
            return f"{target_docker_repository_config().tag_prefix}_db-test-container"
        else:
            return f"db-test-container"

    def get_mapping_of_build_files_and_directories(self):
        return {
            mapping.target: str(mapping.source)
            for mapping in self.test_container_content.build_files_and_directories
        }

    def get_dockerfile(self):
        return str(self.test_container_content.docker_file)

    def is_rebuild_requested(self) -> bool:
        config = build_config()
        return bool(config.force_rebuild)


class DockerTestContainerBuildBase(DockerBuildBase, TestContainerParameter):

    def get_goal_class_map(self) -> Dict[str, DockerAnalyzeImageTask]:
        goal_class_map = {
            "test-container": self.create_child_task(
                task_class=AnalyzeTestContainer,
                test_container_content=self.test_container_content,
            )
        }
        return goal_class_map

    def get_default_goals(self) -> Set[str]:
        goals = {"test-container"}
        return goals

    def get_goals(self):
        goals = {"test-container"}
        return goals


class DockerTestContainerBuild(DockerTestContainerBuildBase):

    def run_task(self):
        build_tasks = self.create_build_tasks(False)
        image_infos_futures = yield from self.run_dependencies(build_tasks)
        image_infos = self.get_values_from_futures(image_infos_futures)
        self.return_object(image_infos)


class DockerTestContainerPush(DockerTestContainerBuildBase, DockerPushParameter):

    def run_task(self):
        build_tasks = self.create_build_tasks(shortcut_build=not self.push_all)
        push_task_creator = PushTaskCreatorFromBuildTasks(self)
        push_tasks = push_task_creator.create_tasks_for_build_tasks(build_tasks)
        image_info_future = yield from self.run_dependencies(push_tasks)
        image_info = self.get_values_from_futures(image_info_future)
        self.return_object(image_info)
